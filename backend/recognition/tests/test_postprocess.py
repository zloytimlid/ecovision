import logging

import pytest

from recognition.models import Recognition
from recognition.services.postprocess import analyze, find_alternatives, load_mapping, normalize

DETECTION = "object-detection"
CLASSIFICATION = "classification"

DETECTION_RAW = {
    "predictions": [
        {"x": 100, "y": 80, "width": 40, "height": 60, "confidence": 0.55, "class": "Battery"},
        {"x": 320, "y": 240, "width": 120, "height": 200, "confidence": 0.91, "class": "plastic_cup", "class_id": 3},
    ],
    "image": {"width": 1280, "height": 960},
}

CLASSIFICATION_RAW = {
    "predictions": [
        {"class": "paper_cup", "confidence": 0.06},
        {"class": "plastic_cup", "confidence": 0.91},
    ],
    "top": "plastic_cup",
    "confidence": 0.91,
}


# --- normalize ----------------------------------------------------------------


def test_normalize_detection():
    assert normalize(DETECTION_RAW, DETECTION) == [
        {
            "model_class": "plastic_cup",
            "confidence": 0.91,
            "bbox": {"x": 320.0, "y": 240.0, "width": 120.0, "height": 200.0},
        },
        {
            "model_class": "battery",
            "confidence": 0.55,
            "bbox": {"x": 100.0, "y": 80.0, "width": 40.0, "height": 60.0},
        },
    ]


def test_normalize_classification():
    assert normalize(CLASSIFICATION_RAW, CLASSIFICATION) == [
        {"model_class": "plastic_cup", "confidence": 0.91, "bbox": None},
        {"model_class": "paper_cup", "confidence": 0.06, "bbox": None},
    ]


def test_normalize_multilabel_classification():
    raw = {"predictions": {"Glass Jar": {"confidence": 0.7}, "metal-can": {"confidence": 0.8}}}
    assert [p["model_class"] for p in normalize(raw, CLASSIFICATION)] == ["metal_can", "glass_jar"]


@pytest.mark.parametrize(
    "raw",
    [
        {"predictions": []},
        {},
        None,
        {"predictions": None},
        {"predictions": [{"class": "x"}, {"confidence": 0.9}, "junk", {"class": "y", "confidence": "?"}]},
    ],
    ids=["empty-list", "no-key", "none", "null", "malformed"],
)
def test_normalize_empty_or_malformed(raw):
    assert normalize(raw, DETECTION) == []


# --- analyze: statuses --------------------------------------------------------


def run_analyze(predictions, model_type=DETECTION):
    return analyze(
        predictions,
        load_mapping(),
        model_type=model_type,
        min_confidence=0.4,
        low_confidence_threshold=0.6,
    )


def prediction(model_class, confidence, bbox=True):
    box = {"x": 10.0, "y": 10.0, "width": 5.0, "height": 5.0} if bbox else None
    return {"model_class": model_class, "confidence": confidence, "bbox": box}


@pytest.mark.django_db
def test_status_not_found_when_no_predictions(seeded):
    result = run_analyze([])
    assert result.status == Recognition.Status.NOT_FOUND
    assert result.top is None and result.category is None and result.objects == []


@pytest.mark.django_db
def test_status_not_found_when_everything_below_min_confidence(seeded):
    result = run_analyze([prediction("plastic_cup", 0.3, bbox=False)], CLASSIFICATION)
    assert result.status == Recognition.Status.NOT_FOUND


@pytest.mark.django_db
def test_status_unmapped_class_is_logged(seeded, caplog):
    caplog.set_level(logging.WARNING)
    result = run_analyze([prediction("space_debris", 0.95), prediction("battery", 0.7)])

    assert result.status == Recognition.Status.UNMAPPED_CLASS
    assert result.top["model_class"] == "space_debris"
    assert result.category is None
    assert "space_debris" in caplog.text


@pytest.mark.django_db
def test_status_low_confidence(seeded):
    result = run_analyze([prediction("plastic_cup", 0.5)])
    assert result.status == Recognition.Status.LOW_CONFIDENCE
    assert result.category.slug == "plastic"


@pytest.mark.django_db
def test_status_ok(seeded):
    result = run_analyze([prediction("glass_jar", 0.6)])
    assert result.status == Recognition.Status.OK
    assert result.category.slug == "glass"


@pytest.mark.django_db
def test_detection_objects_carry_categories(seeded):
    result = run_analyze(normalize(DETECTION_RAW, DETECTION))
    assert result.category.slug == "plastic"
    assert [(o["model_class"], o["category"].slug) for o in result.objects] == [
        ("plastic_cup", "plastic"),
        ("battery", "batteries"),
    ]


@pytest.mark.django_db
def test_classification_has_no_objects(seeded):
    result = run_analyze(normalize(CLASSIFICATION_RAW, CLASSIFICATION), CLASSIFICATION)
    assert result.status == Recognition.Status.OK
    assert result.objects == []


# --- alternatives -------------------------------------------------------------


@pytest.mark.django_db
def test_alternatives_are_unique_limited_and_exclude_top(seeded):
    predictions = [
        prediction("plastic_cup", 0.5),
        prediction("plastic_bottle", 0.45),  # same category as top
        prediction("paper_cup", 0.2),
        prediction("tetra_pak", 0.15),  # same category as paper_cup
        prediction("unknown_thing", 0.12),  # unmapped
        prediction("glass_jar", 0.1),
        prediction("battery", 0.08),
        prediction("cable", 0.05),
    ]
    alternatives = find_alternatives(predictions, load_mapping(), exclude_slug="plastic")
    assert alternatives == [
        {"category_slug": "composite", "name": "Комбинированная упаковка", "confidence": 0.2},
        {"category_slug": "glass", "name": "Стекло", "confidence": 0.1},
        {"category_slug": "batteries", "name": "Батарейки и аккумуляторы", "confidence": 0.08},
    ]
