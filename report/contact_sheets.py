"""Render PDF pages with pdftoppm and tile them into contact sheets for quick visual review."""
import subprocess
import sys
from pathlib import Path

from PIL import Image

pdf = Path(sys.argv[1])
out = Path(sys.argv[2])
dpi = sys.argv[3] if len(sys.argv) > 3 else "60"
per_sheet = int(sys.argv[4]) if len(sys.argv) > 4 else 6
cols = int(sys.argv[5]) if len(sys.argv) > 5 else 3
out.mkdir(parents=True, exist_ok=True)
for old in out.glob("*.png"):
    old.unlink()
subprocess.run([r"C:\poppler\Library\bin\pdftoppm.exe", "-r", dpi, "-png", str(pdf), str(out / "p")], check=True)
pages = sorted(out.glob("p-*.png"))
for s in range(0, len(pages), per_sheet):
    chunk = pages[s:s + per_sheet]
    ims = [Image.open(p).convert("RGB") for p in chunk]
    w, h = ims[0].size
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * w + (cols + 1) * 8, rows * h + (rows + 1) * 8), (120, 120, 120))
    for i, im in enumerate(ims):
        sheet.paste(im, (8 + (i % cols) * (w + 8), 8 + (i // cols) * (h + 8)))
    sheet.save(out / f"sheet_{s // per_sheet + 1:02d}.png")
print(len(pages), "pages ->", len(list(out.glob('sheet_*.png'))), "sheets")
