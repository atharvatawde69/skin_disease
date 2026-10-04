"""Training loop: configurable optimizer, regularization, class weights, early stopping."""
from __future__ import annotations

import json
import random
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import f1_score

from .data import make_loader
from .evaluate import compute_metrics, predict
from .labels import CLASS_CODES, MEAN, STD
from .models import build_model


@dataclass
class Config:
    name: str = "run"
    model: str = "resnet18"        # cnn | resnet18 | resnet50
    pretrained: bool = True        # ImageNet weights (ignored for 'cnn')
    optimizer: str = "adam"        # sgd | momentum | adam | rmsprop
    lr: float = 3e-4
    weight_decay: float = 1e-4     # L2 regularization
    dropout: float = 0.3
    augment: bool = True
    class_weights: bool = True     # weighted cross-entropy
    epochs: int = 15
    patience: int = 5              # early stopping: stop after this many epochs without val improvement
    batch_size: int = 64
    img_size: int = 224
    scheduler: str = "cosine"      # cosine | none
    seed: int = 42
    num_workers: int = 2
    out_dir: str = "outputs"


def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def build_optimizer(params, cfg: Config):
    if cfg.optimizer == "sgd":        # plain gradient descent on mini-batches
        return torch.optim.SGD(params, lr=cfg.lr, weight_decay=cfg.weight_decay)
    if cfg.optimizer == "momentum":   # SGD + momentum
        return torch.optim.SGD(params, lr=cfg.lr, momentum=0.9, weight_decay=cfg.weight_decay)
    if cfg.optimizer == "adam":
        return torch.optim.Adam(params, lr=cfg.lr, weight_decay=cfg.weight_decay)
    if cfg.optimizer == "rmsprop":
        return torch.optim.RMSprop(params, lr=cfg.lr, weight_decay=cfg.weight_decay)
    raise ValueError(f"unknown optimizer {cfg.optimizer}")


def _make_scaler(enabled: bool):
    try:
        return torch.amp.GradScaler("cuda", enabled=enabled)
    except AttributeError:  # torch < 2.3
        return torch.cuda.amp.GradScaler(enabled=enabled)


def fit(cfg: Config, train_ds, val_ds, test_ds, class_weights=None, verbose: bool = True) -> dict:
    """Train with early stopping on validation macro-F1, then score the best epoch on the test set."""
    set_seed(cfg.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    use_amp = device.type == "cuda"
    if use_amp:
        torch.backends.cudnn.benchmark = True

    train_loader = make_loader(train_ds.with_augment(cfg.augment), cfg.batch_size, True, cfg.num_workers)
    val_loader = make_loader(val_ds, cfg.batch_size, False, cfg.num_workers)
    test_loader = make_loader(test_ds, cfg.batch_size, False, cfg.num_workers)

    model = build_model(cfg.model, pretrained=cfg.pretrained, dropout=cfg.dropout).to(device)
    weight = class_weights.to(device) if (cfg.class_weights and class_weights is not None) else None
    criterion = nn.CrossEntropyLoss(weight=weight)
    optimizer = build_optimizer(model.parameters(), cfg)
    scheduler = (torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=cfg.epochs)
                 if cfg.scheduler == "cosine" else None)
    scaler = _make_scaler(use_amp)

    out_dir = Path(cfg.out_dir) / cfg.name
    out_dir.mkdir(parents=True, exist_ok=True)
    ckpt_path = out_dir / "best.pt"

    history = {k: [] for k in ("train_loss", "train_acc", "val_loss", "val_acc", "val_f1", "lr")}
    best_f1, best_epoch, wait = -1.0, 0, 0
    start = time.time()

    for epoch in range(1, cfg.epochs + 1):
        t0 = time.time()
        model.train()
        loss_sum, correct, n = 0.0, 0, 0
        for x, y in train_loader:
            x, y = x.to(device, non_blocking=True), y.to(device, non_blocking=True)
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type=device.type, enabled=use_amp):
                out = model(x)
                loss = criterion(out, y)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            loss_sum += loss.item() * len(y)
            correct += (out.argmax(1) == y).sum().item()
            n += len(y)

        history["lr"].append(optimizer.param_groups[0]["lr"])
        if scheduler:
            scheduler.step()

        val = predict(model, val_loader, device, criterion)
        val_f1 = f1_score(val["y_true"], val["y_pred"], labels=list(range(len(CLASS_CODES))),
                          average="macro", zero_division=0)
        history["train_loss"].append(loss_sum / n)
        history["train_acc"].append(correct / n)
        history["val_loss"].append(val["loss"])
        history["val_acc"].append(float((val["y_true"] == val["y_pred"]).mean()))
        history["val_f1"].append(float(val_f1))

        improved = val_f1 > best_f1
        if improved:
            best_f1, best_epoch, wait = float(val_f1), epoch, 0
            torch.save({"model": model.state_dict(), "cfg": asdict(cfg), "classes": CLASS_CODES,
                        "img_size": cfg.img_size, "mean": MEAN, "std": STD}, ckpt_path)
        else:
            wait += 1

        if verbose:
            print(f"[{cfg.name}] epoch {epoch:02d}/{cfg.epochs} | train loss {history['train_loss'][-1]:.3f} "
                  f"acc {history['train_acc'][-1]:.3f} | val loss {val['loss']:.3f} "
                  f"acc {history['val_acc'][-1]:.3f} f1 {val_f1:.3f} | {time.time() - t0:.0f}s"
                  f"{'  *best*' if improved else ''}")
        if wait >= cfg.patience:
            if verbose:
                print(f"[{cfg.name}] early stopping: no val improvement for {cfg.patience} epochs")
            break

    # Test on the best epoch (not the last one)
    model.load_state_dict(torch.load(ckpt_path, map_location=device)["model"])
    test = predict(model, test_loader, device)
    metrics = compute_metrics(test["y_true"], test["y_pred"])
    result = {"name": cfg.name, "cfg": asdict(cfg), "history": history, "best_epoch": best_epoch,
              "best_val_f1": best_f1, "test": metrics, "ckpt": str(ckpt_path),
              "train_seconds": time.time() - start}
    (out_dir / "result.json").write_text(json.dumps(result, indent=2))
    if verbose:
        print(f"[{cfg.name}] TEST acc {metrics['accuracy']:.3f} | balanced acc {metrics['balanced_accuracy']:.3f} "
              f"| macro-F1 {metrics['macro_f1']:.3f} | melanoma recall {metrics['per_class']['mel']['recall']:.3f}")
    return result
