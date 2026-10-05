"""Numbers quoted in the report, computed from the project code (parameter counts, class weights)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.models import build_model  # noqa: E402

TRAIN_COUNTS = {"akiec": 233, "bcc": 365, "bkl": 775, "df": 76, "mel": 777, "nv": 4730, "vasc": 98}  # Kaggle Step 4 output

if __name__ == "__main__":
    for name in ("cnn", "resnet18", "resnet50"):
        m = build_model(name, pretrained=False)
        print(name, sum(p.numel() for p in m.parameters()))
    n = sum(TRAIN_COUNTS.values())
    print("train total", n)
    for k, c in TRAIN_COUNTS.items():
        print(k, c, round(n / (7 * c), 3))
