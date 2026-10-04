"""HAM10000 data pipeline: metadata, lesion-wise split, cached Dataset, transforms."""
from __future__ import annotations

import copy
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import torch
from PIL import Image
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms as T

from .labels import CLASS_CODES, MEAN, STD


def load_metadata(data_dir) -> pd.DataFrame:
    """Read HAM10000_metadata.csv and attach the image path and integer label.

    The Kaggle zip spreads images over several folders (and may contain duplicate
    folders), so we index every .jpg under data_dir by its file name.
    """
    data_dir = Path(data_dir)
    csv_path = next(data_dir.rglob("HAM10000_metadata.csv"), None)
    if csv_path is None:
        raise FileNotFoundError(f"HAM10000_metadata.csv not found under {data_dir}")

    paths = {p.stem: p for p in data_dir.rglob("*.jpg")}
    df = pd.read_csv(csv_path)
    missing = set(df["image_id"]) - set(paths)
    if missing:
        raise FileNotFoundError(f"{len(missing)} images from the CSV are missing, e.g. {sorted(missing)[:3]}")

    df["path"] = df["image_id"].map(paths).astype(str)
    df["label"] = df["dx"].map({c: i for i, c in enumerate(CLASS_CODES)})
    return df


def _split_lesions(lesions: pd.DataFrame, test_size: float, seed: int):
    try:
        return train_test_split(lesions, test_size=test_size, stratify=lesions["dx"], random_state=seed)
    except ValueError:  # a class has too few lesions to stratify (only happens on tiny debug subsets)
        return train_test_split(lesions, test_size=test_size, random_state=seed)


def split_by_lesion(df: pd.DataFrame, val_size=0.15, test_size=0.15, seed=42) -> pd.DataFrame:
    """Add a 'split' column (train/val/test), splitting on lesion_id, not on image.

    HAM10000 has several photos of the same lesion. Splitting per image would put
    near-identical photos in both train and test and inflate the test score.
    """
    lesions = df.groupby("lesion_id", as_index=False).agg(dx=("dx", "first"))
    train_val, test = _split_lesions(lesions, test_size, seed)
    train, val = _split_lesions(train_val, val_size / (1 - test_size), seed)

    lesion_to_split = {}
    for name, part in (("train", train), ("val", val), ("test", test)):
        lesion_to_split.update({lid: name for lid in part["lesion_id"]})

    df = df.copy()
    df["split"] = df["lesion_id"].map(lesion_to_split)

    sets = {s: set(df.loc[df["split"] == s, "lesion_id"]) for s in ("train", "val", "test")}
    assert not (sets["train"] & sets["val"] or sets["train"] & sets["test"] or sets["val"] & sets["test"]), \
        "lesion leakage between splits"
    return df


def compute_class_weights(train_df: pd.DataFrame) -> torch.Tensor:
    """Inverse-frequency weights: rare classes (df, vasc) count more in the loss than nv."""
    counts = train_df["label"].value_counts().reindex(range(len(CLASS_CODES))).fillna(1).values
    weights = counts.sum() / (len(CLASS_CODES) * counts)
    return torch.tensor(weights, dtype=torch.float32)


def build_transform(img_size: int, augment: bool):
    steps = [T.Resize((img_size, img_size))]
    if augment:
        steps += [
            T.RandomResizedCrop(img_size, scale=(0.75, 1.0), ratio=(0.9, 1.1)),
            T.RandomHorizontalFlip(),
            T.RandomVerticalFlip(),
            T.RandomRotation(30),
            T.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.02),
        ]
    steps += [T.ToTensor(), T.Normalize(MEAN, STD)]
    return T.Compose(steps)


class HamDataset(Dataset):
    """Skin-lesion images. Images are resized once and kept in RAM so every epoch is fast."""

    def __init__(self, df: pd.DataFrame, img_size: int = 224, augment: bool = False, cache: bool = True):
        self.paths = df["path"].tolist()
        self.labels = df["label"].astype(int).tolist()
        self.img_size = img_size
        self.transform = build_transform(img_size, augment)
        self.images = None
        if cache:
            with ThreadPoolExecutor(max_workers=8) as pool:
                self.images = list(pool.map(self._load, self.paths))

    def _load(self, path):
        return Image.open(path).convert("RGB").resize((self.img_size, self.img_size), Image.BILINEAR)

    def with_augment(self, augment: bool) -> "HamDataset":
        """Same cached images, different transform (lets experiments toggle augmentation for free)."""
        other = copy.copy(self)
        other.transform = build_transform(self.img_size, augment)
        return other

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, i):
        img = self.images[i] if self.images is not None else self._load(self.paths[i])
        return self.transform(img), self.labels[i]


def make_loader(ds: Dataset, batch_size: int, shuffle: bool, num_workers: int = 2) -> DataLoader:
    return DataLoader(
        ds,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
        persistent_workers=num_workers > 0,
    )
