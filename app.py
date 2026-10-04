"""DermaScan: Flask demo for the HAM10000 skin-lesion classifier (ResNet + Grad-CAM).

Run:  python app.py        (needs models/best.pt, produced by notebooks/train.ipynb)
Env:  MODEL_PATH, HOST (default 127.0.0.1), FLASK_DEBUG=1 for the dev reloader.
"""
import base64
import io
import os
import threading
from pathlib import Path

import numpy as np
import torch
from flask import Flask, render_template, request
from PIL import Image, UnidentifiedImageError
from torchvision import transforms as T

from src.gradcam import GradCAM, overlay_cam
from src.labels import CLASS_CODES, CLASS_NAMES, NEEDS_ATTENTION
from src.models import build_model, gradcam_target_layer

MODEL_PATH = os.environ.get("MODEL_PATH", "models/best.pt")
LOW_CONFIDENCE = 0.5

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


BUNDLE = load_model(MODEL_PATH)


def to_data_uri(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def analyse(image: Image.Image) -> dict:
    x = BUNDLE["transform"](image).unsqueeze(0)
    with _lock:
        cam, _, probs = BUNDLE["cam"](x)

    shown = image.copy()
    shown.thumbnail((512, 512))
    order = np.argsort(probs)[::-1][:3]
    top = [{"code": BUNDLE["classes"][i], "name": CLASS_NAMES[BUNDLE["classes"][i]], "prob": float(probs[i]),
            "attention": BUNDLE["classes"][i] in NEEDS_ATTENTION} for i in order]
    return {"top": top, "low_conf": top[0]["prob"] < LOW_CONFIDENCE,
            "image": to_data_uri(shown), "heatmap": to_data_uri(overlay_cam(shown, cam)), "model": BUNDLE["name"]}


def page(**ctx):
    return render_template("index.html", model_ready=BUNDLE is not None, **ctx)


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
