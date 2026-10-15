"""Turn a raw Roboflow response into a recognition status, category and objects."""

import logging
from dataclasses import dataclass, field

from catalog.models import ModelClassMapping, normalize_class_name
from recognition.models import Recognition

from .roboflow_client import DETECTION

logger = logging.getLogger(__name__)

BBOX_KEYS = ("x", "y", "width", "height")
MAX_ALTERNATIVES = 3


@dataclass
class Analysis:
    status: str
    top: dict | None = None  # the best prediction, see normalize()
    category: object = None  # WasteCategory of the top prediction
    # Detected objects (detection models only): predictions with a "category" key.
    objects: list = field(default_factory=list)


def load_mapping():
    """Return {normalized model class: ModelClassMapping} with categories preloaded."""
    return {m.model_class: m for m in ModelClassMapping.objects.select_related("category")}


def normalize(raw, model_type):
    """
    Convert a Roboflow response (object detection or classification) into
    [{"model_class", "confidence", "bbox"}] sorted by confidence, highest first.
    bbox is {"x", "y", "width", "height"} (center and size in pixels) or None.
    """
    raw_predictions = (raw or {}).get("predictions") or []
    if isinstance(raw_predictions, dict):
        # Multi-label classification: {"class_name": {"confidence": 0.9}, ...}
        raw_predictions = [
            {"class": name, **value}
            for name, value in raw_predictions.items()
            if isinstance(value, dict)
        ]

    predictions = []
    for item in raw_predictions:
        if not isinstance(item, dict):
            continue
        model_class = normalize_class_name(str(item.get("class") or ""))
        try:
            confidence = float(item.get("confidence"))
        except (TypeError, ValueError):
            continue
        if not model_class:
            continue

        bbox = None
        if model_type == DETECTION and all(key in item for key in BBOX_KEYS):
            try:
                bbox = {key: float(item[key]) for key in BBOX_KEYS}
            except (TypeError, ValueError):
                bbox = None
        predictions.append({"model_class": model_class, "confidence": confidence, "bbox": bbox})

    predictions.sort(key=lambda p: p["confidence"], reverse=True)
    return predictions


def analyze(predictions, mapping, *, model_type, min_confidence, low_confidence_threshold):
    """
    Pick the status and the final category from normalized predictions.

    Predictions below min_confidence do not count as found items (for detection
    Roboflow already drops them; for classification they only serve as alternatives).
    """
    found = [p for p in predictions if p["confidence"] >= min_confidence]
    if not found:
        return Analysis(status=Recognition.Status.NOT_FOUND)

    objects = []
    if model_type == DETECTION:
        objects = [
            {**p, "category": _category(mapping, p["model_class"])} for p in found if p["bbox"]
        ]

    top = found[0]
    entry = mapping.get(top["model_class"])
    if entry is None:
        logger.warning("Unmapped model class %r (confidence %.2f)", top["model_class"], top["confidence"])
        return Analysis(status=Recognition.Status.UNMAPPED_CLASS, top=top, objects=objects)

    if top["confidence"] < low_confidence_threshold:
        status = Recognition.Status.LOW_CONFIDENCE
    else:
        status = Recognition.Status.OK
    return Analysis(status=status, top=top, category=entry.category, objects=objects)


def find_alternatives(predictions, mapping, exclude_slug=None, limit=MAX_ALTERNATIVES):
    """Up to `limit` other unique categories, each with its highest confidence."""
    seen = {exclude_slug} if exclude_slug else set()
    alternatives = []
    for prediction in predictions:  # already sorted by confidence
        category = _category(mapping, prediction["model_class"])
        if category is None or category.slug in seen:
            continue
        seen.add(category.slug)
        alternatives.append(
            {
                "category_slug": category.slug,
                "name": category.name,
                "confidence": prediction["confidence"],
            }
        )
        if len(alternatives) == limit:
            break
    return alternatives


def _category(mapping, model_class):
    entry = mapping.get(model_class)
    return entry.category if entry else None
