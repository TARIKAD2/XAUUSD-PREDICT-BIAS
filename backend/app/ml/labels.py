"""Stable mapping between string market classes and model-safe integer labels."""
from __future__ import annotations

import numpy as np
from sklearn.preprocessing import LabelEncoder

CLASS_ORDER = ["BEARISH", "BULLISH"]


def fit_label_encoder(y):
    encoder = LabelEncoder()
    present = sorted(set(str(v) for v in y))
    if set(present) <= set(CLASS_ORDER):
        encoder.fit(CLASS_ORDER)
        encoder.classes_ = np.asarray(CLASS_ORDER)
        return encoder
    encoder.fit(present)
    return encoder


def encode_labels(encoder: LabelEncoder, y):
    return encoder.transform([str(v) for v in y])


def decode_labels(encoder: LabelEncoder, y_encoded):
    return encoder.inverse_transform(y_encoded)
