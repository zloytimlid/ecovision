from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from recognition.models import DetectedObject, Recognition
from recognition.services.roboflow_client import (
    RoboflowError,
    RoboflowNotConfigured,
    RoboflowTimeout,
)

from .conftest import make_image

pytestmark = pytest.mark.django_db

URL = reverse("recognition:recognize")


def upload(data=None, name="photo.jpg", content_type="image/jpeg"):
    return SimpleUploadedFile(name, data if data is not None else make_image(), content_type)


def post(client, client_id, data=None, **kwargs):
    headers = {"X-Client-Id": client_id} if client_id is not None else {}
    payload = {"image": upload(data, **kwargs)} if data is not False else {}
    return client.post(URL, payload, headers=headers)


def detection(*items):
    return {
        "predictions": [
            {"x": 50, "y": 40, "width": 20, "height": 30, "class": cls, "confidence": conf}
            for cls, conf in items
        ],
        "image": {"width": 64, "height": 48},
    }


def assert_error(response, status_code, code):
    assert response.status_code == status_code, response.content
    body = response.json()
    assert body["error"]["code"] == code
    assert body["error"]["message"]


# --- success paths --------------------------------------------------------------


def test_successful_recognition(client, seeded, client_id, fake_roboflow):
    fake_roboflow.response = detection(("plastic_cup", 0.91), ("paper_cup", 0.45))

    response = post(client, client_id, make_image(size=(2560, 1920)))

    assert response.status_code == 201, response.content
    body = response.json()
    assert body["status"] == "ok"
    assert body["image_size"] == {"width": 1280, "height": 960}
    assert body["image_url"].startswith("http://testserver/media/recognitions/")
    assert body["top"]["model_class"] == "plastic_cup"
    assert body["top"]["display_name"] == "Пластиковый стаканчик"
    assert body["top"]["confidence"] == 0.91
    category = body["top"]["category"]
    assert category["slug"] == "plastic"
    assert category["bin_color"] == "#F5C400"
    assert set(category) == {
        "slug", "name", "bin_name", "bin_color", "icon", "preparation_steps", "do_not", "is_hazardous",
    }
    assert body["objects"] == [
        {
            "model_class": "plastic_cup",
            "confidence": 0.91,
            "bbox": {"x": 50.0, "y": 40.0, "width": 20.0, "height": 30.0},
            "category_slug": "plastic",
        },
        {
            "model_class": "paper_cup",
            "confidence": 0.45,
            "bbox": {"x": 50.0, "y": 40.0, "width": 20.0, "height": 30.0},
            "category_slug": "composite",
        },
    ]
    assert body["alternatives"] == [
        {"category_slug": "composite", "name": "Комбинированная упаковка", "confidence": 0.45}
    ]
    assert body["has_hazardous"] is False
    assert body["feedback"] is None
    assert isinstance(body["inference_ms"], int)

    recognition = Recognition.objects.get(pk=body["id"])
    assert str(recognition.client_id) == client_id
    assert recognition.category.slug == "plastic"
    assert recognition.raw_response == fake_roboflow.response
    assert recognition.detected_objects.count() == 2
    assert recognition.image.storage.exists(recognition.image.name)

    # The resized JPEG is what goes to Roboflow.
    with Image.open(BytesIO(fake_roboflow.calls[0])) as sent:
        assert sent.format == "JPEG" and sent.size == (1280, 960)


def test_low_confidence_returns_alternatives(client, seeded, client_id, fake_roboflow):
    fake_roboflow.response = detection(("plastic_cup", 0.5), ("tetra_pak", 0.42))
    body = post(client, client_id).json()
    assert body["status"] == "low_confidence"
    assert body["top"]["category"]["slug"] == "plastic"
    assert [a["category_slug"] for a in body["alternatives"]] == ["composite"]


def test_hazardous_object_sets_flag(client, seeded, client_id, fake_roboflow):
    fake_roboflow.response = detection(("plastic_bottle", 0.9), ("battery", 0.6))
    body = post(client, client_id).json()
    assert body["status"] == "ok"
    assert body["top"]["category"]["slug"] == "plastic"
    assert body["has_hazardous"] is True


def test_not_found(client, seeded, client_id, fake_roboflow):
    fake_roboflow.response = {"predictions": []}
    response = post(client, client_id)
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "not_found"
    assert body["top"] is None
    assert body["objects"] == [] and body["alternatives"] == []
    assert Recognition.objects.get(pk=body["id"]).status == "not_found"


def test_unmapped_class(client, seeded, client_id, fake_roboflow):
    fake_roboflow.response = detection(("Mystery Box", 0.88))
    body = post(client, client_id).json()
    assert body["status"] == "unmapped_class"
    assert body["top"] == {
        "model_class": "mystery_box",
        "display_name": None,
        "confidence": 0.88,
        "category": None,
    }
    assert body["objects"][0]["category_slug"] is None


def test_classification_model(client, seeded, client_id, fake_roboflow, settings):
    settings.ROBOFLOW_MODEL_TYPE = "classification"
    fake_roboflow.response = {
        "predictions": [{"class": "battery", "confidence": 0.93}, {"class": "phone", "confidence": 0.05}],
        "top": "battery",
        "confidence": 0.93,
    }
    body = post(client, client_id).json()
    assert body["status"] == "ok"
    assert body["top"]["category"]["slug"] == "batteries"
    assert body["objects"] == []
    assert body["has_hazardous"] is True
    assert body["alternatives"] == [
        {"category_slug": "electronics", "name": "Электроника", "confidence": 0.05}
    ]
    assert DetectedObject.objects.count() == 0


# --- errors ---------------------------------------------------------------------


@pytest.mark.parametrize("header", [None, "", "not-a-uuid"], ids=["absent", "empty", "invalid"])
def test_missing_or_invalid_client_id(client, seeded, fake_roboflow, header):
    assert_error(post(client, header), 400, "missing_client_id")
    assert fake_roboflow.calls == []


def test_broken_file(client, seeded, client_id, fake_roboflow):
    response = post(client, client_id, b"this is not an image", name="photo.jpg")
    assert_error(response, 400, "invalid_image")
    assert fake_roboflow.calls == []
    assert Recognition.objects.count() == 0


def test_unsupported_format(client, seeded, client_id, fake_roboflow):
    response = post(client, client_id, make_image(image_format="GIF"), name="a.gif", content_type="image/gif")
    assert_error(response, 400, "invalid_image")


def test_missing_image_field(client, seeded, client_id, fake_roboflow):
    assert_error(post(client, client_id, data=False), 400, "invalid_image")


def test_file_too_large(client, seeded, client_id, fake_roboflow, settings):
    settings.MAX_UPLOAD_BYTES = 1024
    response = post(client, client_id, make_image(size=(400, 400)) + b"\0" * 2048)
    assert_error(response, 413, "file_too_large")
    assert fake_roboflow.calls == []


@pytest.mark.parametrize(
    "error, status_code, code",
    [
        (RoboflowTimeout("timeout"), 504, "model_timeout"),
        (RoboflowError("HTTP 500"), 502, "model_unavailable"),
        (RoboflowNotConfigured("no key"), 502, "model_unavailable"),
    ],
)
def test_model_errors(client, seeded, client_id, fake_roboflow, error, status_code, code):
    fake_roboflow.error = error
    assert_error(post(client, client_id), status_code, code)
    assert Recognition.objects.count() == 0


def test_get_is_not_allowed(client, client_id):
    response = client.get(URL, headers={"X-Client-Id": client_id})
    assert_error(response, 405, "method_not_allowed")
