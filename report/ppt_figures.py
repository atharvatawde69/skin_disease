"""Figures made for the presentation: large-text system diagram (>= 17 pt at final size) and colour sampling helper.

Run:  python report/ppt_figures.py
Writes report/figures/ppt_system_diagram.png (7.4 x 5.0 in at 300 dpi, transparent background).
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

OUT = Path(__file__).resolve().parent / "figures"
families = {f.name for f in font_manager.fontManager.ttflist}
FONT = "Times New Roman" if "Times New Roman" in families else "DejaVu Serif"
plt.rcParams["font.family"] = FONT

INK, DARK, TINT, MID, RED_TINT, RED = "#1b1b1b", "#1f4e79", "#e4f1f9", "#1e88c8", "#f8e9e6", "#b03a2e"


def box(ax, x, y, w, h, text, fc, ec, bold=False, fs=18, color=INK):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12", fc=fc, ec=ec, lw=1.6))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal",
            color=color, linespacing=1.15)


def arrow(ax, x0, y0, x1, y1, color=INK):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="-|>", color=color, lw=2.0, shrinkA=0, shrinkB=0))


def system_diagram():
    W, H = 7.4, 5.0
    fig, ax = plt.subplots(figsize=(W, H))
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    fig.patch.set_alpha(0)
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis("off")

    bw, bh = 3.2, 0.78
    xl, xr = 0.08, 4.12
    ys = [3.45, 2.33, 1.21, 0.09]

    ax.text(xl + bw / 2, 4.68, "Training (once, Kaggle GPU)", ha="center", va="center", fontsize=18, fontweight="bold", color=DARK)
    ax.text(xr + bw / 2, 4.68, "Web app (Flask)", ha="center", va="center", fontsize=18, fontweight="bold", color=DARK)

    left = ["HAM10000 images", "Split by lesion\n(70 / 15 / 15)", "Train CNN and\nResNet-18", "Keep best model"]
    right = ["User uploads image", "Saved ResNet-18 gives\n7 probabilities", "Grad-CAM heatmap", "Result, guidance\nand warnings"]
    for y, t in zip(ys, left):
        box(ax, xl, y, bw, bh, t, TINT, DARK)
    for y, t in zip(ys, right):
        box(ax, xr, y, bw, bh, t, "white", MID)
    for i in range(3):
        arrow(ax, xl + bw / 2, ys[i] - 0.02, xl + bw / 2, ys[i + 1] + bh + 0.02)
        arrow(ax, xr + bw / 2, ys[i] - 0.02, xr + bw / 2, ys[i + 1] + bh + 0.02)
    # the best model is saved and loaded by the web app's prediction step
    mid_x = (xl + bw + xr) / 2
    y_from, y_to = ys[3] + bh / 2, ys[1] + bh / 2
    ax.plot([xl + bw + 0.02, mid_x], [y_from, y_from], color=RED, lw=2.2, solid_capstyle="butt")
    ax.plot([mid_x, mid_x], [y_from, y_to], color=RED, lw=2.2, solid_capstyle="butt")
    arrow(ax, mid_x, y_to, xr - 0.02, y_to, color=RED)

    fig.savefig(OUT / "ppt_system_diagram.png", dpi=300, transparent=True, bbox_inches=None, pad_inches=0)
    plt.close(fig)


if __name__ == "__main__":
    print("font:", FONT)
    system_diagram()
    print("saved", OUT / "ppt_system_diagram.png")
