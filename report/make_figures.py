"""Build the figures used by the lab report: diagrams (matplotlib), app screenshots (headless Chrome), result plots.

Run with the project's Python environment:  python report/make_figures.py
Needs: matplotlib, Pillow, Flask + the trained models/best.pt (for the app screenshots), Google Chrome.
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402
from PIL import Image, ImageChops  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "report" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
DOWNLOADS = Path.home() / "Downloads"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

INK, TEAL, TEAL_FILL, GREY_FILL, OCHRE, OCHRE_FILL = "#1f2a2e", "#2c6e6a", "#e3efed", "#eef0ee", "#b07d1f", "#f8f1e1"
plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": INK})


def box(ax, x, y, w, h, text, fc=GREY_FILL, ec=INK, fs=7.2, bold_first=True):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.25,rounding_size=1.2", fc=fc, ec=ec, lw=0.9))
    lines = text.split("\n")
    n = len(lines)
    pt_per_unit = ax.figure.get_figheight() * 72 / ax.get_ylim()[1]
    step = fs * 1.32 / pt_per_unit  # line height of 1.32 x font size, independent of the figure scale
    top = y + h / 2 + (n - 1) * step / 2
    for i, line in enumerate(lines):
        ax.text(x + w / 2, top - i * step, line, ha="center", va="center", fontsize=fs,
                fontweight="bold" if (i == 0 and bold_first) else "normal")


def arrow(ax, x0, y0, x1, y1, color=INK, style="-|>"):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle=style, color=color, lw=1.0, shrinkA=0, shrinkB=0))


def new_ax(w, h, xmax, ymax):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, xmax)
    ax.set_ylim(0, ymax)
    ax.axis("off")
    return fig, ax


# ---------------------------------------------------------------- Fig 2.1 block diagram
def fig_block_diagram():
    fig, ax = new_ax(7.6, 5.0, 100, 66)
    bw, gap = 17.4, 2.25
    xs = [2 + i * (bw + gap) for i in range(5)]

    ax.text(2, 63.5, "TRAINING PIPELINE  (Kaggle notebook, NVIDIA T4 GPU)", fontsize=7.5, fontweight="bold", color=TEAL)
    top = [("HAM10000\n10,015 images\n+ metadata", GREY_FILL),
           ("Pre-processing\nresize 224 x 224\nImageNet\nnormalisation", GREY_FILL),
           ("Lesion-wise split\n70% train\n15% validation\n15% test", TEAL_FILL),
           ("Augmentation\n(train set only)\nflips, rotation,\ncrop, colour", GREY_FILL),
           ("Model training\nCNN / ResNet-18\nweighted loss,\nearly stopping", TEAL_FILL)]
    for x, (t, fc) in zip(xs, top):
        box(ax, x, 43, bw, 16, t, fc=fc, fs=6.9)
    for i in range(4):
        arrow(ax, xs[i] + bw + 0.4, 51.5, xs[i + 1] - 0.4, 51.5)

    ax.text(2, 38.5, "EVALUATION AND MODEL SELECTION", fontsize=7.5, fontweight="bold", color=TEAL)
    box(ax, xs[4], 21, bw, 14, "Evaluation\nval macro-F1\n(model selection),\ntest metrics", fc=OCHRE_FILL, ec=OCHRE, fs=6.9)
    box(ax, xs[2], 21, bw, 14, "Best checkpoint\nmodels/best.pt\nResNet-18,\nRMSProp", fc=OCHRE_FILL, ec=OCHRE, fs=6.9)
    arrow(ax, xs[4] + bw / 2, 43.4, xs[4] + bw / 2, 35.6)
    arrow(ax, xs[4] - 0.4, 28.5, xs[2] + bw + 0.4, 28.5)

    ax.text(2, 17.5, "INFERENCE PIPELINE  (Flask web application)", fontsize=7.5, fontweight="bold", color=TEAL)
    bot = [("User uploads\nimage\n(PNG / JPG)", GREY_FILL),
           ("Pre-processing\nresize, normalise\n(in memory)", GREY_FILL),
           ("ResNet-18\nforward pass,\nsoftmax over\n7 classes", TEAL_FILL),
           ("Grad-CAM and\nguidance rules,\nuncertainty\nchecks", GREY_FILL),
           ("Result page\nprobabilities,\nheatmap,\nnext steps", GREY_FILL)]
    for x, (t, fc) in zip(xs, bot):
        box(ax, x, 0.5, bw, 15, t, fc=fc, fs=6.9)
    for i in range(4):
        arrow(ax, xs[i] + bw + 0.4, 8, xs[i + 1] - 0.4, 8)
    arrow(ax, xs[2] + bw / 2, 20.4, xs[2] + bw / 2, 16.0, color=OCHRE)
    fig.savefig(OUT / "fig2_1_block_diagram.png", dpi=300, bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)


# ---------------------------------------------------------------- Fig 2.2 baseline CNN
def fig_cnn():
    fig, ax = new_ax(7.6, 2.5, 100, 28)
    labels = [("Input\n3 x 224 x 224", GREY_FILL),
              ("Block 1\nConv 3x3, 32\nBN, ReLU\nMaxPool 2\n32x112x112", TEAL_FILL),
              ("Block 2\nConv 3x3, 64\nBN, ReLU\nMaxPool 2\n64x56x56", TEAL_FILL),
              ("Block 3\nConv 3x3, 128\nBN, ReLU\nMaxPool 2\n128x28x28", TEAL_FILL),
              ("Block 4\nConv 3x3, 256\nBN, ReLU\nMaxPool 2\n256x14x14", TEAL_FILL),
              ("Global\naverage\npooling\n256", GREY_FILL),
              ("Dropout 0.5\nLinear\n256 to 7", OCHRE_FILL),
              ("Softmax\n7 classes", GREY_FILL)]
    w, gap = 10.4, 1.9
    x = 1.7
    centers = []
    for text, fc in labels:
        box(ax, x, 3, w, 21, text, fc=fc, fs=6.2)
        centers.append(x)
        x += w + gap
    for i in range(len(labels) - 1):
        arrow(ax, centers[i] + w + 0.3, 13.5, centers[i + 1] - 0.3, 13.5)
    fig.savefig(OUT / "fig2_2_cnn_architecture.png", dpi=300, bbox_inches="tight", pad_inches=0.06)
    plt.close(fig)


# ---------------------------------------------------------------- Fig 2.3 ResNet-18 + residual block
def fig_resnet():
    fig, ax = new_ax(7.6, 5.4, 100, 72)
    ax.text(2, 70, "(a) ResNet-18 as used in this project", fontsize=8, fontweight="bold", color=TEAL)
    w, gap, h = 17, 2.75, 14
    row1 = [("Input\n3 x 224 x 224", GREY_FILL), ("conv1 7x7, 64, /2\nBN, ReLU\n64 x 112 x 112", GREY_FILL),
            ("MaxPool 3x3, /2\n64 x 56 x 56", GREY_FILL), ("layer1\n2 x BasicBlock, 64\n64 x 56 x 56", TEAL_FILL),
            ("layer2\n2 x BasicBlock, 128\n128 x 28 x 28", TEAL_FILL)]
    row2 = [("layer3\n2 x BasicBlock, 256\n256 x 14 x 14", TEAL_FILL), ("layer4\n2 x BasicBlock, 512\n512 x 7 x 7", TEAL_FILL),
            ("Global average\npooling\n512", GREY_FILL), ("Dropout 0.3\nLinear 512 to 7\n(new head)", OCHRE_FILL),
            ("Softmax\n7 classes", GREY_FILL)]
    xs = [2 + i * (w + gap) for i in range(5)]
    for x, (t, fc) in zip(xs, row1):
        box(ax, x, 51, w, h, t, fc=fc, fs=6.4)
    for x, (t, fc) in zip(xs, row2):
        box(ax, x, 33, w, h, t, fc=fc, fs=6.4)
    for i in range(4):
        arrow(ax, xs[i] + w + 0.3, 58, xs[i + 1] - 0.3, 58)
        arrow(ax, xs[i] + w + 0.3, 40, xs[i + 1] - 0.3, 40)
    # row1 -> row2 elbow
    ax.plot([xs[4] + w / 2, xs[4] + w / 2], [50.6, 48.5], color=INK, lw=1.0)
    ax.plot([xs[4] + w / 2, xs[0] + w / 2], [48.5, 48.5], color=INK, lw=1.0)
    arrow(ax, xs[0] + w / 2, 48.5, xs[0] + w / 2, 47.4)

    ax.text(2, 27, "(b) Basic residual block (skip connection)", fontsize=8, fontweight="bold", color=TEAL)
    yb, hb = 8, 11
    bx = [14, 29, 41.5, 56, 68.5]
    names = [("Conv 3x3", 11.5), ("BN, ReLU", 11.5), ("Conv 3x3", 11.5), ("BN", 8)]
    box(ax, 2, yb, 7, hb, "x", fc=GREY_FILL, fs=8, bold_first=False)
    cx = [13, 27.5, 42, 56.5]
    widths = [12, 12, 12, 8]
    for x, wd, (t, _) in zip(cx, widths, names):
        box(ax, x, yb, wd, hb, t, fc=TEAL_FILL, fs=6.8, bold_first=False)
    ax.add_patch(plt.Circle((72, yb + hb / 2), 3.0, fc="white", ec=INK, lw=1.0))
    ax.text(72, yb + hb / 2, "+", ha="center", va="center", fontsize=11)
    box(ax, 80, yb, 8, hb, "ReLU", fc=GREY_FILL, fs=6.8, bold_first=False)
    box(ax, 92, yb, 7, hb, "out", fc=GREY_FILL, fs=7.5, bold_first=False)
    ym = yb + hb / 2
    arrow(ax, 9.3, ym, 12.7, ym)
    arrow(ax, 25.3, ym, 27.2, ym)
    arrow(ax, 39.7, ym, 41.7, ym)
    arrow(ax, 54.3, ym, 56.2, ym)
    arrow(ax, 64.8, ym, 68.9, ym)
    arrow(ax, 75.2, ym, 79.7, ym)
    arrow(ax, 88.3, ym, 91.7, ym)
    # skip path
    ax.plot([5.5, 5.5], [yb - 0.2, 3.5], color=OCHRE, lw=1.3)
    ax.plot([5.5, 72], [3.5, 3.5], color=OCHRE, lw=1.3)
    arrow(ax, 72, 3.5, 72, yb + hb / 2 - 3.1, color=OCHRE)
    ax.text(38, 0.8, "identity (skip connection):  out = ReLU( F(x) + x )", fontsize=6.8, color=OCHRE, ha="center")
    fig.savefig(OUT / "fig2_3_resnet18.png", dpi=300, bbox_inches="tight", pad_inches=0.06)
    plt.close(fig)


# ---------------------------------------------------------------- app screenshots
def trim(img: Image.Image, pad=16) -> Image.Image:
    bg = Image.new(img.mode, img.size, img.getpixel((2, 2)))
    bbox = ImageChops.difference(img, bg).getbbox()
    if not bbox:
        return img
    l, t, r, b = bbox
    return img.crop((max(l - pad, 0), max(t - pad, 0), min(r + pad, img.width), min(b + pad, img.height)))


def app_screenshots():
    sys.path.insert(0, str(ROOT))
    os.chdir(ROOT)
    import app as web

    client = web.app.test_client()
    static_uri = (ROOT / "static").as_uri() + "/"
    pages = {"home": client.get("/").get_data(as_text=True)}
    with open(ROOT / "samples" / "sample_mel.jpg", "rb") as f:
        pages["result"] = client.post("/", data={"file": (f, "sample.jpg")},
                                      content_type="multipart/form-data").get_data(as_text=True)

    hide = {
        "home": ".site-header,#result,#abcde,#about,.site-footer{display:none!important}"
                ".intro{padding-top:8px}",
        "result": ".site-header,.intro,#analyze,#abcde,#about,.site-footer{display:none!important}"
                  ".no-print{display:none!important}",
    }
    tmp = Path(tempfile.mkdtemp())
    for name, html in pages.items():
        html = html.replace("/static/", static_uri).replace("</head>", f"<style>{hide[name]}</style></head>")
        page = tmp / f"{name}.html"
        page.write_text(html, encoding="utf-8")
        png = tmp / f"{name}.png"
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--window-size=940,2300", "--force-device-scale-factor=2",
                        "--blink-settings=preferredColorScheme=1", f"--screenshot={png}", page.as_uri()],
                       capture_output=True, timeout=180)
        img = trim(Image.open(png).convert("RGB"))
        img.save(OUT / ("fig3_2_app_upload.png" if name == "home" else "fig3_3_app_result.png"))
    shutil.rmtree(tmp, ignore_errors=True)


def copy_results():
    names = {"models_comparison.png": "fig4_1_models_comparison.png", "optimizers.png": "fig4_2_optimizers.png",
             "regularization.png": "fig4_3_regularization.png", "loss.png": "fig4_4_loss.png",
             "confusion_matrix.png": "fig4_5_confusion_matrix.png", "gradcam.png": "fig4_6_gradcam.png"}
    for src, dst in names.items():
        shutil.copy(DOWNLOADS / src, OUT / dst)


if __name__ == "__main__":
    fig_block_diagram()
    fig_cnn()
    fig_resnet()
    copy_results()
    app_screenshots()
    for p in sorted(OUT.glob("*.png")):
        print(p.name, Image.open(p).size)
