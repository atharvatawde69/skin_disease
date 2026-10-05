"""Create demo samples that the model has provably never seen.

How: re-run the project's lesion-wise split (seed 42) on the original HAM10000 metadata (Harvard Dataverse), check that it
reproduces the split sizes printed by the Kaggle notebook, keep only TEST-split images, download them from the ISIC archive
(same file names as HAM10000), run the trained model, and keep a mix: clear correct predictions plus some mistakes.

Run:  python report/make_samples.py        (needs models/best.pt and internet; writes samples/*.jpg and samples/README.md)
"""
import io
import shutil
import sys
import urllib.request
from pathlib import Path

import pandas as pd
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SAMPLES = ROOT / "samples"
META_URL = "https://dataverse.harvard.edu/api/access/datafile/4338392"
IMG_URL = "https://isic-archive.s3.amazonaws.com/images/{}.jpg"
PER_CLASS_POOL = 24          # test images per class to download and score
KEEP_CORRECT, KEEP_WRONG = 2, 1

# split sizes and per-class test counts printed by the Kaggle notebook (Step 4)
EXPECTED_SPLIT = {"train": 7054, "val": 1464, "test": 1497}
EXPECTED_TEST = {"akiec": 51, "bcc": 77, "bkl": 157, "df": 22, "mel": 168, "nv": 1000, "vasc": 22}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=60).read()


def load_split():
    raw = fetch(META_URL).decode("utf-8")
    df = pd.read_csv(io.StringIO(raw), sep="\t")
    df.columns = [c.strip().strip('"') for c in df.columns]
    from src.data import split_by_lesion

    df = split_by_lesion(df[["lesion_id", "image_id", "dx"]].assign(label=0))
    sizes = df["split"].value_counts().to_dict()
    test_counts = df[df.split == "test"]["dx"].value_counts().to_dict()
    assert sizes == EXPECTED_SPLIT, f"split sizes differ from the Kaggle run: {sizes}"
    assert test_counts == EXPECTED_TEST, f"test class counts differ from the Kaggle run: {test_counts}"
    print("split reproduced exactly:", sizes)
    return df


def main():
    df = load_split()
    test = df[df.split == "test"]

    import app as web  # loads models/best.pt

    rows = []
    for code, group in test.groupby("dx"):
        pool = group.sample(min(PER_CLASS_POOL, len(group)), random_state=7)
        for _, r in pool.iterrows():
            try:
                img = Image.open(io.BytesIO(fetch(IMG_URL.format(r.image_id)))).convert("RGB")
            except Exception as exc:  # a missing file on the archive: skip it
                print("skip", r.image_id, exc)
                continue
            res = web.analyse(img)
            top = res["top"][0]
            rows.append({"image_id": r.image_id, "true": code, "pred": top["code"], "conf": top["prob"],
                         "mel_prob": res["mel_prob"], "img": img})
        print(code, "scored")

    chosen = []
    for code in sorted({r["true"] for r in rows}):
        mine = [r for r in rows if r["true"] == code]
        right = sorted((r for r in mine if r["pred"] == code), key=lambda r: -r["conf"])
        wrong = sorted((r for r in mine if r["pred"] != code), key=lambda r: -r["conf"])
        chosen += right[:KEEP_CORRECT] + wrong[:KEEP_WRONG]

    if SAMPLES.exists():
        shutil.rmtree(SAMPLES)
    SAMPLES.mkdir()
    lines = ["| File | True class | Model says | Confidence | Melanoma probability |", "|---|---|---|---|---|"]
    counters = {}
    for r in chosen:
        counters[r["true"]] = counters.get(r["true"], 0) + 1
        name = f"{r['true']}_{counters[r['true']]}_{r['image_id']}.jpg"
        r["img"].save(SAMPLES / name, quality=95)
        verdict = "correct" if r["pred"] == r["true"] else "WRONG"
        lines.append(f"| {name} | {r['true']} | {r['pred']} ({verdict}) | {r['conf'] * 100:.0f}% | {r['mel_prob'] * 100:.0f}% |")
    readme = (
        "# Demo samples\n\n"
        "Real HAM10000 dermoscopy images taken from the **test split** of the lesion-wise split (seed 42), so the model "
        "never saw them or any other photo of the same lesions during training or validation. The split was reproduced "
        "from the original HAM10000 metadata and checked against the counts printed by the Kaggle notebook "
        "(7,054 / 1,464 / 1,497 images).\n\n"
        "For each class there are up to two images the model gets right with the highest confidence and one it gets "
        "wrong or is least sure about, so you can show both the strengths and the weaknesses. The last two columns were "
        "produced by the trained model in `models/best.pt`.\n\n"
        "Images: Tschandl et al., HAM10000 (CC BY-NC 4.0), downloaded from the ISIC archive.\n\n" + "\n".join(lines) + "\n")
    (SAMPLES / "README.md").write_text(readme, encoding="utf-8")
    print(f"saved {len(chosen)} samples to {SAMPLES}")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
