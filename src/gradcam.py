"""Grad-CAM: highlight the image regions that pushed the model toward a class.

Idea: take the last conv feature maps, weight each map by how much the class score
changes when that map changes (the mean gradient), sum, keep the positive part.
"""
from __future__ import annotations

import matplotlib
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image


class GradCAM:
    def __init__(self, model, target_layer):
        self.model = model
        self.activations = None
        self.gradients = None
        self._handle = target_layer.register_forward_hook(self._on_forward)

    def _on_forward(self, module, inputs, output):
        self.activations = output.detach()
        # grab the gradient flowing back into this feature map
        output.register_hook(lambda g: setattr(self, "gradients", g.detach()))

    def __call__(self, x: torch.Tensor, class_idx: int | None = None):
        """x: (1,3,H,W). Returns (cam in [0,1] as HxW array, class index used, class probabilities)."""
        self.model.eval()
        self.model.zero_grad(set_to_none=True)
        with torch.enable_grad():
            logits = self.model(x)
            if class_idx is None:
                class_idx = int(logits.argmax(1))
            logits[0, class_idx].backward()
        weights = self.gradients.mean(dim=(2, 3), keepdim=True)
        cam = F.relu((weights * self.activations).sum(dim=1))[0]
        cam = cam - cam.min()
        cam = cam / (cam.max() + 1e-8)
        return cam.cpu().numpy(), class_idx, logits.detach().softmax(1)[0].cpu().numpy()

    def remove(self):
        self._handle.remove()


def overlay_cam(image: Image.Image, cam: np.ndarray, alpha: float = 0.45) -> Image.Image:
    """Blend the heatmap over the original image."""
    heat = Image.fromarray((cam * 255).astype(np.uint8)).resize(image.size, Image.BICUBIC)
    colored = matplotlib.colormaps["jet"](np.asarray(heat) / 255.0)[..., :3]
    blended = (1 - alpha) * np.asarray(image.convert("RGB")) / 255.0 + alpha * colored
    return Image.fromarray((blended.clip(0, 1) * 255).astype(np.uint8))
