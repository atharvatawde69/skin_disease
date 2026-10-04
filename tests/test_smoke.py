"""End-to-end smoke test on tiny fake data (no download, no GPU, ~1 minute on CPU).

Checks: metadata loading, lesion-wise split without leakage, both models train and save,
metrics, Grad-CAM, and the Flask app serving a prediction.
Run:  python -m pytest tests -q
"""
import io
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import HamDataset, compute_class_weights, load_metadata, split_by_lesion  # noqa: E402
from src.evaluate import results_table  # noqa: E402
from src.labels import CLASS_CODES  # noqa: E402
from src.train import Config, fit  # noqa: E402


@pytest.fixture(scope="module")
def fake_data(tmp_path_factory):
    """7 classes x 20 images; every lesion has 2 photos, like the real dataset's duplicates."""
    root = tmp_path_factory.mktemp("ham")
    (root / "HAM10000_images_part_1").mkdir()
    rng = np.random.default_rng(0)
    rows = []
    for ci, code in enumerate(CLASS_CODES):
        for k in range(20):
            image_id = f"ISIC_{ci}{k:03d}"
            base = np.full((48, 64, 3), 30 + ci * 30, dtype=np.uint8)
            noise = rng.integers(0, 40, size=base.shape, dtype=np.uint8)
            Image.fromarray(base + noise).save(root / "HAM10000_images_part_1" / f"{image_id}.jpg")
            rows.append({"lesion_id": f"HAM_{ci}{k // 2:03d}", "image_id": image_id, "dx": code})
    pd.DataFrame(rows).to_csv(root / "HAM10000_metadata.csv", index=False)
    return root


def test_split_has_no_lesion_leakage(fake_data):
    df = split_by_lesion(load_metadata(fake_data))
    assert set(df["split"]) == {"train", "val", "test"}
    for a, b in (("train", "val"), ("train", "test"), ("val", "test")):
        assert not set(df[df.split == a].lesion_id) & set(df[df.split == b].lesion_id)
    assert len(compute_class_weights(df[df.split == "train"])) == len(CLASS_CODES)


def test_training_gradcam_and_app(fake_data, tmp_path, monkeypatch):
    df = split_by_lesion(load_metadata(fake_data))
    ds = {s: HamDataset(df[df.split == s], img_size=64) for s in ("train", "val", "test")}
    weights = compute_class_weights(df[df.split == "train"])

    results = {}
    for name, model, pretrained in (("cnn", "cnn", False), ("res", "resnet18", False)):
        cfg = Config(name=name, model=model, pretrained=pretrained, epochs=2, patience=2, batch_size=16,
                     img_size=64, num_workers=0, out_dir=str(tmp_path / "out"))
        results[name] = fit(cfg, ds["train"], ds["val"], ds["test"], weights, verbose=False)
        assert Path(results[name]["ckpt"]).exists()
        assert 0.0 <= results[name]["test"]["macro_f1"] <= 1.0

    table = results_table(results)
    assert list(table["run"]) == ["cnn", "res"]

    # Flask app on the trained ResNet checkpoint (also exercises Grad-CAM via analyse())
    monkeypatch.setenv("MODEL_PATH", results["res"]["ckpt"])
    sys.modules.pop("app", None)
    import app as web

    client = web.app.test_client()
    assert client.get("/").status_code == 200

    buf = io.BytesIO()
    Image.new("RGB", (120, 90), (120, 60, 60)).save(buf, format="PNG")
    buf.seek(0)
    resp = client.post("/", data={"file": (buf, "lesion.png")}, content_type="multipart/form-data")
    page = resp.get_data(as_text=True)
    assert resp.status_code == 200 and "Prediction:" in page and "Grad-CAM" in page

    bad = client.post("/", data={"file": (io.BytesIO(b"not an image"), "x.txt")}, content_type="multipart/form-data")
    assert "not a readable image" in bad.get_data(as_text=True)

    empty = client.post("/", data={}, content_type="multipart/form-data")
    assert "choose an image" in empty.get_data(as_text=True)
