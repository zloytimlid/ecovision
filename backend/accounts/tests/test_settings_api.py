from io import BytesIO

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image
from rest_framework.authtoken.models import Token

from accounts.models import Profile
from recognition.models import Recognition
from recognition.tests.conftest import make_image

pytestmark = pytest.mark.django_db

User = get_user_model()
PASSWORD = "Sorting-Waste-42"
ME = reverse("accounts:me")
AVATAR = reverse("accounts:avatar")
PASSWORD_URL = reverse("accounts:password")


@pytest.fixture
def user():
    return User.objects.create_user(username="anna", password=PASSWORD)


@pytest.fixture
def token(user):
    return Token.objects.create(user=user).key


def auth(token):
    return {"Authorization": f"Token {token}"}


def patch(client, token, payload):
    return client.patch(ME, payload, content_type="application/json", headers=auth(token))


# --- username and e-mail ----------------------------------------------------------


def test_update_username_and_email(client, user, token):
    response = patch(client, token, {"username": "anna_eco", "email": "anna@example.com"})
    assert response.status_code == 200, response.content
    body = response.json()
    assert body["username"] == "anna_eco"
    assert body["email"] == "anna@example.com"
    user.refresh_from_db()
    assert (user.username, user.email) == ("anna_eco", "anna@example.com")


def test_username_can_change_case_of_own_name(client, token):
    assert patch(client, token, {"username": "Anna"}).status_code == 200


def test_username_taken_by_someone_else(client, token):
    User.objects.create_user(username="boris", password=PASSWORD)
    response = patch(client, token, {"username": "BORIS"})
    assert response.status_code == 400
    assert "username" in response.json()["error"]["details"]


@pytest.mark.parametrize("payload", [{"username": "bad name!"}, {"email": "not-an-email"}])
def test_invalid_values(client, token, payload):
    assert patch(client, token, payload).status_code == 400


def test_settings_require_login(client):
    assert client.patch(ME, {}, content_type="application/json").status_code == 401
    assert client.post(AVATAR).status_code == 401
    assert client.post(PASSWORD_URL).status_code == 401


# --- avatar -------------------------------------------------------------------------


def upload_avatar(client, token, data, name="a.png", content_type="image/png"):
    return client.post(AVATAR, {"avatar": SimpleUploadedFile(name, data, content_type)}, headers=auth(token))


def test_avatar_is_cropped_to_square_jpeg(client, user, token):
    response = upload_avatar(client, token, make_image(size=(800, 400), image_format="PNG"))
    assert response.status_code == 200, response.content
    avatar_url = response.json()["avatar_url"]
    assert avatar_url.startswith("http://testserver/media/avatars/")

    profile = Profile.objects.get(user=user)
    with profile.avatar.open("rb") as file, Image.open(BytesIO(file.read())) as image:
        assert image.format == "JPEG"
        assert image.size == (256, 256)
    assert client.get(ME, headers=auth(token)).json()["avatar_url"] == avatar_url


def test_replacing_avatar_removes_old_file(client, user, token):
    upload_avatar(client, token, make_image())
    profile = Profile.objects.get(user=user)
    old_name, storage = profile.avatar.name, profile.avatar.storage

    upload_avatar(client, token, make_image(color=(0, 0, 255)))
    profile.refresh_from_db()
    assert profile.avatar.name != old_name
    assert not storage.exists(old_name)
    assert storage.exists(profile.avatar.name)


def test_delete_avatar(client, user, token):
    upload_avatar(client, token, make_image())
    name = Profile.objects.get(user=user).avatar.name
    response = client.delete(AVATAR, headers=auth(token))
    assert response.status_code == 200
    assert response.json()["avatar_url"] is None
    assert not Profile.objects.get(user=user).avatar
    assert not Profile.objects.get(user=user).avatar.storage.exists(name)


def test_avatar_rejects_non_images(client, token):
    response = upload_avatar(client, token, b"not an image", name="a.jpg", content_type="image/jpeg")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_image"


# --- password -----------------------------------------------------------------------


def change_password(client, token, current, new):
    return client.post(
        PASSWORD_URL,
        {"current_password": current, "new_password": new},
        content_type="application/json",
        headers=auth(token),
    )


def test_change_password_rotates_token(client, user, token):
    response = change_password(client, token, PASSWORD, "New-Sorting-Pass-7")
    assert response.status_code == 200
    new_token = response.json()["token"]
    assert new_token != token

    user.refresh_from_db()
    assert user.check_password("New-Sorting-Pass-7")
    assert client.get(ME, headers=auth(token)).status_code == 401  # other sessions logged out
    assert client.get(ME, headers=auth(new_token)).status_code == 200


def test_change_password_wrong_current(client, user, token):
    response = change_password(client, token, "wrong-password", "New-Sorting-Pass-7")
    assert response.status_code == 400
    assert "current_password" in response.json()["error"]["details"]
    user.refresh_from_db()
    assert user.check_password(PASSWORD)


def test_change_password_weak_new(client, token):
    response = change_password(client, token, PASSWORD, "123")
    assert response.status_code == 400
    assert "new_password" in response.json()["error"]["details"]


# --- account deletion ------------------------------------------------------------------


def test_delete_account_requires_password(client, user, token):
    response = client.delete(ME, {"password": "wrong"}, content_type="application/json", headers=auth(token))
    assert response.status_code == 400
    assert User.objects.filter(pk=user.pk).exists()


def test_delete_account_removes_data(client, user, token, django_capture_on_commit_callbacks):
    upload_avatar(client, token, make_image())
    avatar = Profile.objects.get(user=user).avatar
    avatar_name, storage = avatar.name, avatar.storage
    Recognition.objects.create(
        client_id="11111111-2222-4333-8444-555555555555",
        user=user,
        image=SimpleUploadedFile("p.jpg", make_image(), "image/jpeg"),
        image_width=64,
        image_height=48,
        status=Recognition.Status.NOT_FOUND,
    )

    with django_capture_on_commit_callbacks(execute=True):
        response = client.delete(ME, {"password": PASSWORD}, content_type="application/json", headers=auth(token))

    assert response.status_code == 204
    assert not User.objects.filter(pk=user.pk).exists()
    assert not Recognition.objects.exists()
    assert not storage.exists(avatar_name)
