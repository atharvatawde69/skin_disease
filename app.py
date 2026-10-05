"""DermaScan: Flask demo for the HAM10000 skin-lesion classifier (ResNet + Grad-CAM).

Run:  python app.py        (needs models/best.pt, produced by notebooks/train.ipynb)
Env:  MODEL_PATH, HOST (default 127.0.0.1), FLASK_DEBUG=1 for the dev reloader.
"""
import base64
import io
import json
import os
import threading
from pathlib import Path

import numpy as np
import torch
from flask import Flask, render_template, request
from PIL import Image, UnidentifiedImageError
from torchvision import transforms as T

from src.gradcam import GradCAM, heatmap_image
from src.knowledge import CLASS_INFO, RISK_LABEL
from src.labels import CLASS_NAMES
from src.models import build_model, gradcam_target_layer

ROOT = Path(__file__).parent
MODEL_PATH = os.environ.get("MODEL_PATH", "models/best.pt")
LOW_CONFIDENCE = 0.5   # below this the model is unsure
CLOSE_CALL = 0.15      # top-1 and top-2 closer than this is a toss-up
MEL_HINT = 0.15        # show a melanoma warning above this probability even if another class ranks first

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # reject uploads over 10 MB

_lock = threading.Lock()  # Grad-CAM keeps hook state on the model, so one request at a time


def load_model(path):
    """Rebuild the network from the config stored inside the checkpoint."""
    path = Path(path)
    if not path.exists():
        return None
    ckpt = torch.load(path, map_location="cpu", weights_only=True)
    cfg = ckpt["cfg"]
    model = build_model(cfg["model"], pretrained=False, dropout=cfg["dropout"])
    model.load_state_dict(ckpt["model"])
    model.eval()
    size = ckpt["img_size"]
    return {
        "name": cfg["model"],
        "classes": ckpt["classes"],
        "transform": T.Compose([T.Resize((size, size)), T.ToTensor(), T.Normalize(ckpt["mean"], ckpt["std"])]),
        "cam": GradCAM(model, gradcam_target_layer(model)),
    }


def load_model_card():
    """Metrics shown in the 'About the model' panel (model_card.json next to this file)."""
    path = ROOT / "model_card.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


BUNDLE = load_model(MODEL_PATH)
CARD = load_model_card()


def to_data_uri(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def analyse(image: Image.Image) -> dict:
    x = BUNDLE["transform"](image).unsqueeze(0)
    with _lock:
        cam, _, probs = BUNDLE["cam"](x)

    classes = BUNDLE["classes"]
    shown = image.copy()
    shown.thumbnail((512, 512))
    order = np.argsort(probs)[::-1][:3]
    top = [{"code": classes[i], "name": CLASS_NAMES[classes[i]], "prob": float(probs[i])} for i in order]

    best = top[0]
    info = CLASS_INFO[best["code"]]
    mel_prob = float(probs[classes.index("mel")])
    low_conf = best["prob"] < LOW_CONFIDENCE
    mel_hint = best["code"] != "mel" and mel_prob >= MEL_HINT

    # an unsure or melanoma-suspicious result must never carry a reassuring "harmless" badge
    risk, risk_label = info["risk"], RISK_LABEL[info["risk"]]
    if risk == "low" and (low_conf or mel_hint):
        risk, risk_label = "medium", "Uncertain result: consider getting it checked"

    return {
        "top": top,
        "info": info,
        "risk": risk,
        "risk_label": risk_label,
        "mel_prob": mel_prob,
        "low_conf": low_conf,
        "close_call": top[1]["name"] if not low_conf and best["prob"] - top[1]["prob"] < CLOSE_CALL else None,
        "mel_hint": mel_hint,
        "image": to_data_uri(shown),
        "heat": to_data_uri(heatmap_image(cam, shown.size)),
        "model": BUNDLE["name"],
    }


def page(**ctx):
    return render_template("index.html", model_ready=BUNDLE is not None, card=CARD, class_names=CLASS_NAMES, **ctx)


@app.errorhandler(413)
def too_large(_):
    return page(error="That file is larger than 10 MB."), 413


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return page()
    if BUNDLE is None:
        return page(error="No trained model found. Train one with notebooks/train.ipynb and put it in models/best.pt.")

    file = request.files.get("file")
    if file is None or file.filename == "":
        return page(error="Please choose an image first.")
    try:
        image = Image.open(file.stream).convert("RGB")
    except (UnidentifiedImageError, OSError):
        return page(error="That file is not a readable image (use PNG or JPG).")

    return page(result=analyse(image))


if __name__ == "__main__":
    app.run(host=os.environ.get("HOST", "127.0.0.1"), port=5000, debug=os.environ.get("FLASK_DEBUG") == "1")
