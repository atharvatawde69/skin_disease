"""Models: a small CNN built from scratch (baseline) and ResNet transfer learning."""
from __future__ import annotations

import torch.nn as nn
from torchvision import models

NUM_CLASSES = 7


def _conv_block(in_ch: int, out_ch: int, use_bn: bool) -> nn.Sequential:
    layers = [nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=1, bias=not use_bn)]
    if use_bn:
        layers.append(nn.BatchNorm2d(out_ch))
    layers += [nn.ReLU(inplace=True), nn.MaxPool2d(2)]
    return nn.Sequential(*layers)


class SimpleCNN(nn.Module):
    """4 x (Conv -> BatchNorm -> ReLU -> MaxPool), global average pooling, dropout, linear."""

    def __init__(self, num_classes: int = NUM_CLASSES, dropout: float = 0.5, use_bn: bool = True):
        super().__init__()
        chans = [3, 32, 64, 128, 256]
        self.features = nn.Sequential(*[_conv_block(chans[i], chans[i + 1], use_bn) for i in range(4)])
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.classifier = nn.Sequential(nn.Flatten(), nn.Dropout(dropout), nn.Linear(chans[-1], num_classes))

    def forward(self, x):
        return self.classifier(self.pool(self.features(x)))


def build_resnet(name: str = "resnet18", pretrained: bool = True, dropout: float = 0.3,
                 num_classes: int = NUM_CLASSES) -> nn.Module:
    """torchvision ResNet with the 1000-class head swapped for Dropout + Linear(num_classes)."""
    builders = {
        "resnet18": (models.resnet18, models.ResNet18_Weights.DEFAULT),
        "resnet50": (models.resnet50, models.ResNet50_Weights.DEFAULT),
    }
    build, weights = builders[name]
    net = build(weights=weights if pretrained else None)
    net.fc = nn.Sequential(nn.Dropout(dropout), nn.Linear(net.fc.in_features, num_classes))
    return net


def build_model(name: str, pretrained: bool = True, dropout: float = 0.3) -> nn.Module:
    if name == "cnn":
        return SimpleCNN(dropout=dropout)
    return build_resnet(name, pretrained=pretrained, dropout=dropout)


def gradcam_target_layer(model: nn.Module) -> nn.Module:
    """Last convolutional stage: where the network still has spatial information."""
    if hasattr(model, "layer4"):  # ResNet
        return model.layer4[-1]
    return model.features[-1]  # SimpleCNN
