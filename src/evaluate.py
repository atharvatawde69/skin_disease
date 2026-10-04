"""Metrics and plots. Accuracy alone is misleading on HAM10000 (67% of images are 'nv')."""
from __future__ import annotations

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import (accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score,
                             precision_recall_fscore_support)

from .labels import CLASS_CODES


@torch.no_grad()
def predict(model, loader, device, criterion=None) -> dict:
    """Run the model over a loader; returns labels, predictions, probabilities and mean loss."""
    model.eval()
    ys, probs, total_loss, n = [], [], 0.0, 0
    for x, y in loader:
        x, y = x.to(device, non_blocking=True), y.to(device)
        out = model(x)
        if criterion is not None:
            total_loss += criterion(out, y).item() * len(y)
        n += len(y)
        ys.append(y.cpu())
        probs.append(out.float().softmax(1).cpu())
    y_true = torch.cat(ys).numpy()
    probs = torch.cat(probs).numpy()
    return {"y_true": y_true, "y_pred": probs.argmax(1), "probs": probs, "loss": total_loss / max(n, 1)}


def compute_metrics(y_true, y_pred) -> dict:
    labels = list(range(len(CLASS_CODES)))
    prec, rec, f1, support = precision_recall_fscore_support(y_true, y_pred, labels=labels, zero_division=0)
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)),
        "per_class": {
            c: {"precision": float(prec[i]), "recall": float(rec[i]), "f1": float(f1[i]), "support": int(support[i])}
            for i, c in enumerate(CLASS_CODES)
        },
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=labels).tolist(),
    }


def results_table(results: dict) -> pd.DataFrame:
    """One row per experiment. Melanoma recall is shown separately: missing a melanoma is the costly error."""
    rows = []
    for name, r in results.items():
        cfg, t = r["cfg"], r["test"]
        rows.append({
            "run": name, "model": cfg["model"], "pretrained": cfg["pretrained"], "optimizer": cfg["optimizer"],
            "lr": cfg["lr"], "wd": cfg["weight_decay"], "dropout": cfg["dropout"], "augment": cfg["augment"],
            "class_w": cfg["class_weights"], "best_epoch": r["best_epoch"], "val_f1": round(r["best_val_f1"], 4),
            "test_acc": round(t["accuracy"], 4), "test_bal_acc": round(t["balanced_accuracy"], 4),
            "test_macro_f1": round(t["macro_f1"], 4), "mel_recall": round(t["per_class"]["mel"]["recall"], 4),
            "minutes": round(r["train_seconds"] / 60, 1),
        })
    return pd.DataFrame(rows)


def plot_history(histories: dict, title: str = ""):
    """Loss and validation macro-F1 curves for one or more runs."""
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    for name, h in histories.items():
        epochs = range(1, len(h["train_loss"]) + 1)
        axes[0].plot(epochs, h["train_loss"], label=name)
        axes[1].plot(epochs, h["val_loss"], label=name)
        axes[2].plot(epochs, h["val_f1"], label=name)
    for ax, t in zip(axes, ("Train loss", "Validation loss", "Validation macro-F1")):
        ax.set_title(t)
        ax.set_xlabel("epoch")
        ax.grid(alpha=0.3)
    axes[0].legend(fontsize=8)
    fig.suptitle(title)
    fig.tight_layout()
    return fig


def plot_confusion_matrix(cm, normalize: bool = True, title: str = "Confusion matrix"):
    import matplotlib.pyplot as plt

    cm = np.array(cm, dtype=float)
    shown = cm / cm.sum(axis=1, keepdims=True).clip(min=1) if normalize else cm
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    im = ax.imshow(shown, cmap="Blues", vmin=0, vmax=1 if normalize else None)
    ax.set_xticks(range(len(CLASS_CODES)), CLASS_CODES)
    ax.set_yticks(range(len(CLASS_CODES)), CLASS_CODES)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title(title)
    for i in range(len(CLASS_CODES)):
        for j in range(len(CLASS_CODES)):
            txt = f"{shown[i, j]:.2f}" if normalize else f"{int(cm[i, j])}"
            ax.text(j, i, txt, ha="center", va="center", fontsize=8,
                    color="white" if shown[i, j] > 0.5 else "black")
    fig.colorbar(im, ax=ax, fraction=0.046)
    fig.tight_layout()
    return fig
