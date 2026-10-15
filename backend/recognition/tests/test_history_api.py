import uuid

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from catalog.models import WasteCategory
from recognition.models import Feedback, Recognition

from .conftest import make_image

pytestmark = pytest.mark.django_db


def make_recognition(client_id, **kwargs):
    options = {
        "client_id": client_id,
        "image": SimpleUploadedFile("p.jpg", make_image(), "image/jpeg"),
        "image_width": 64,
        "image_height": 48,
        "status": Recognition.Status.OK,
        "top_class": "plastic_cup",
        "top_confidence": 0.9,
        "category": WasteCategory.objects.get(slug="plastic"),
        "raw_response": {"predictions": []},
        **kwargs,
    }
    return Recognition.objects.create(**options)


def detail_url(recognition_id):
    return reverse("recognition:recognition-detail", args=[recognition_id])


def feedback_url(recognition_id):
    return reverse("recognition:recognition-feedback", args=[recognition_id])


@pytest.fixture
def mine(seeded, client_id):
    return make_recognition(client_id)


@pytest.fixture
def foreign(seeded):
    return make_recognition(str(uuid.uuid4()))


def get(client, url, client_id):
    return client.get(url, headers={"X-Client-Id": client_id})


# --- history --------------------------------------------------------------------


def test_history_shows_only_own_records(client, client_id, mine, foreign):
    response = get(client, reverse("recognition:recognition-list"), client_id)
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    item = body["results"][0]
    assert item["id"] == str(mine.id)
    assert item["category"]["slug"] == "plastic"
    assert item["image_url"].startswith("http://testserver/media/")
    assert item["feedback"] is None


def test_history_is_paginated_by_20(client, client_id, seeded):
    for _ in range(21):
        make_recognition(client_id)
    url = reverse("recognition:recognition-list")
    first = get(client, url, client_id).json()
    assert len(first["results"]) == 20 and first["next"]
    assert len(get(client, url + "?page=2", client_id).json()["results"]) == 1


def test_history_requires_client_id(client, seeded):
    response = client.get(reverse("recognition:recognition-list"))
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "missing_client_id"


def test_detail_of_own_record(client, client_id, mine):
    body = get(client, detail_url(mine.id), client_id).json()
    assert body["id"] == str(mine.id)
    assert body["top"]["category"]["slug"] == "plastic"


@pytest.mark.parametrize("method", ["get", "delete", "feedback"])
def test_foreign_record_is_404(client, client_id, foreign, method):
    headers = {"X-Client-Id": client_id}
    if method == "get":
        response = client.get(detail_url(foreign.id), headers=headers)
    elif method == "delete":
        response = client.delete(detail_url(foreign.id), headers=headers)
    else:
        response = client.post(
            feedback_url(foreign.id), {"is_correct": True}, content_type="application/json", headers=headers
        )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
    assert Recognition.objects.filter(pk=foreign.pk).exists()


def test_bad_id_is_404(client, client_id, seeded):
    assert get(client, detail_url("not-a-uuid"), client_id).status_code == 404


def test_delete_removes_record_and_photo(client, client_id, mine, django_capture_on_commit_callbacks):
    storage, name = mine.image.storage, mine.image.name
    with django_capture_on_commit_callbacks(execute=True):
        response = client.delete(detail_url(mine.id), headers={"X-Client-Id": client_id})
    assert response.status_code == 204
    assert not Recognition.objects.filter(pk=mine.pk).exists()
    assert not storage.exists(name)


# --- feedback -------------------------------------------------------------------


def post_feedback(client, client_id, recognition, payload):
    return client.post(
        feedback_url(recognition.id), payload, content_type="application/json",
        headers={"X-Client-Id": client_id},
    )


def test_negative_feedback_requires_category(client, client_id, mine):
    response = post_feedback(client, client_id, mine, {"is_correct": False})
    assert response.status_code == 400
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert "correct_category" in error["details"]


def test_unknown_category_is_rejected(client, client_id, mine):
    response = post_feedback(client, client_id, mine, {"is_correct": False, "correct_category": "nope"})
    assert response.status_code == 400


def test_feedback_is_saved_and_overwritten(client, client_id, mine):
    response = post_feedback(
        client, client_id, mine,
        {"is_correct": False, "correct_category": "composite", "comment": "это бумажный стаканчик"},
    )
    assert response.status_code == 200
    assert response.json()["correct_category"] == "composite"

    response = post_feedback(client, client_id, mine, {"is_correct": True, "correct_category": "glass"})
    assert response.status_code == 200
    assert response.json()["correct_category"] is None

    feedback = Feedback.objects.get()
    assert feedback.is_correct is True and feedback.correct_category is None
    detail = get(client, detail_url(mine.id), client_id).json()
    assert detail["feedback"]["is_correct"] is True


# --- health & throttling ---------------------------------------------------------


def test_health(client, settings):
    assert client.get(reverse("recognition:health")).json() == {"status": "ok", "model_configured": True}
    settings.ROBOFLOW_API_KEY = ""
    assert client.get(reverse("recognition:health")).json()["model_configured"] is False


def test_recognize_is_throttled(client, seeded, client_id, fake_roboflow, monkeypatch):
    monkeypatch.setattr("recognition.throttling.RecognizeRateThrottle.THROTTLE_RATES", {"recognize": "2/min"})
    url = reverse("recognition:recognize")
    statuses = []
    for _ in range(3):
        payload = {"image": SimpleUploadedFile("p.jpg", make_image(), "image/jpeg")}
        statuses.append(client.post(url, payload, headers={"X-Client-Id": client_id}).status_code)
    assert statuses == [201, 201, 429]

    response = client.post(url, {}, headers={"X-Client-Id": client_id})
    assert response.json()["error"]["code"] == "throttled"
