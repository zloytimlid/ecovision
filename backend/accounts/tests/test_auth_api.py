import uuid

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.authtoken.models import Token

from recognition.models import Recognition
from recognition.tests.conftest import make_image

pytestmark = pytest.mark.django_db

User = get_user_model()
PASSWORD = "Sorting-Waste-42"


def register(client, username="anna", password=PASSWORD, client_id=None):
    headers = {"X-Client-Id": client_id} if client_id else {}
    return client.post(
        reverse("accounts:register"),
        {"username": username, "password": password},
        content_type="application/json",
        headers=headers,
    )


def login(client, username="anna", password=PASSWORD, client_id=None):
    headers = {"X-Client-Id": client_id} if client_id else {}
    return client.post(
        reverse("accounts:login"),
        {"username": username, "password": password},
        content_type="application/json",
        headers=headers,
    )


def auth(token, client_id=None):
    headers = {"Authorization": f"Token {token}"}
    if client_id:
        headers["X-Client-Id"] = client_id
    return headers


def make_recognition(client_id, user=None):
    return Recognition.objects.create(
        client_id=client_id,
        user=user,
        image=SimpleUploadedFile("p.jpg", make_image(), "image/jpeg"),
        image_width=64,
        image_height=48,
        status=Recognition.Status.NOT_FOUND,
    )


# --- registration & login --------------------------------------------------------


def test_register_returns_token_and_user(client):
    response = register(client)
    assert response.status_code == 201
    body = response.json()
    assert body["user"]["username"] == "anna"
    assert Token.objects.get(user__username="anna").key == body["token"]
    assert User.objects.get(username="anna").check_password(PASSWORD)


def test_register_rejects_weak_password(client):
    response = register(client, password="123")
    assert response.status_code == 400
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert "password" in error["details"]
    assert not User.objects.exists()


def test_register_rejects_taken_username_case_insensitive(client):
    register(client)
    response = register(client, username="ANNA")
    assert response.status_code == 400
    assert "username" in response.json()["error"]["details"]


def test_login(client):
    token = register(client).json()["token"]
    response = login(client)
    assert response.status_code == 200
    assert response.json()["token"] == token


def test_login_ignores_username_case(client):
    register(client, username="Anna")
    assert login(client, username="aNNA").status_code == 200


def test_login_with_wrong_password(client):
    register(client)
    response = login(client, password="wrong-password")
    assert response.status_code == 400
    assert response.json()["error"]["message"] == "Неверное имя пользователя или пароль."


def test_me_requires_auth(client):
    response = client.get(reverse("accounts:me"))
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "not_authenticated"


def test_me(client):
    token = register(client).json()["token"]
    body = client.get(reverse("accounts:me"), headers=auth(token)).json()
    assert body["username"] == "anna"
    assert body["recognitions_count"] == 0


def test_logout_invalidates_token(client):
    token = register(client).json()["token"]
    assert client.post(reverse("accounts:logout"), headers=auth(token)).status_code == 204
    response = client.get(reverse("accounts:me"), headers=auth(token))
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "authentication_failed"


def test_auth_endpoints_are_throttled(client, settings, monkeypatch):
    monkeypatch.setattr("accounts.views.AuthRateThrottle.THROTTLE_RATES", {"auth": "2/min"})
    statuses = [login(client, password="x").status_code for _ in range(3)]
    assert statuses == [400, 400, 429]


# --- recognitions and accounts ---------------------------------------------------


def test_device_history_is_claimed_on_register(client):
    device = str(uuid.uuid4())
    mine = make_recognition(device)
    other = make_recognition(str(uuid.uuid4()))

    register(client, client_id=device)

    mine.refresh_from_db()
    other.refresh_from_db()
    assert mine.user.username == "anna"
    assert other.user is None


def test_account_history_is_shared_across_devices(client):
    phone, laptop = str(uuid.uuid4()), str(uuid.uuid4())
    token = register(client, client_id=phone).json()["token"]
    user = User.objects.get(username="anna")
    from_phone = make_recognition(phone, user=user)
    make_recognition(laptop)  # anonymous record on the laptop, not claimed yet

    url = reverse("recognition:recognition-list")
    body = client.get(url, headers=auth(token, client_id=laptop)).json()
    assert [r["id"] for r in body["results"]] == [str(from_phone.id)]

    detail = reverse("recognition:recognition-detail", args=[from_phone.id])
    assert client.get(detail, headers=auth(token, client_id=laptop)).status_code == 200


def test_claimed_records_are_hidden_from_anonymous_device(client):
    device = str(uuid.uuid4())
    record = make_recognition(device)
    register(client, client_id=device)

    url = reverse("recognition:recognition-list")
    assert client.get(url, headers={"X-Client-Id": device}).json()["count"] == 0
    detail = reverse("recognition:recognition-detail", args=[record.id])
    assert client.get(detail, headers={"X-Client-Id": device}).status_code == 404


def test_recognize_attaches_user(client, seeded, client_id, fake_roboflow):
    token = register(client).json()["token"]
    response = client.post(
        reverse("recognition:recognize"),
        {"image": SimpleUploadedFile("p.jpg", make_image(), "image/jpeg")},
        headers=auth(token, client_id=client_id),
    )
    assert response.status_code == 201
    assert Recognition.objects.get(pk=response.json()["id"]).user.username == "anna"


def test_invalid_token_is_rejected(client, client_id):
    response = client.get(reverse("recognition:recognition-list"), headers=auth("bogus", client_id))
    assert response.status_code == 401
