import pytest
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import clear_url_caches, reverse

from filestore.models import StoredFile
from filestore.storage import DatabaseStorage
from recognition.models import Recognition
from recognition.tests.conftest import make_image

pytestmark = pytest.mark.django_db


@pytest.fixture
def db_media(settings):
    """Switch the default storage and the /media/ URLs to the database."""
    settings.MEDIA_STORAGE = "db"
    settings.STORAGES = {
        **settings.STORAGES,
        "default": {"BACKEND": "filestore.storage.DatabaseStorage"},
    }
    import importlib

    import config.urls

    importlib.reload(config.urls)
    clear_url_caches()
    yield
    settings.MEDIA_STORAGE = "files"
    importlib.reload(config.urls)
    clear_url_caches()


def test_save_open_size_delete():
    storage = DatabaseStorage()
    name = storage.save("recognitions/2026/10/a.jpg", ContentFile(b"jpeg-bytes"))

    assert name == "recognitions/2026/10/a.jpg"
    assert storage.exists(name)
    assert storage.size(name) == len(b"jpeg-bytes")
    with storage.open(name) as file:
        assert file.read() == b"jpeg-bytes"
    assert StoredFile.objects.get(name=name).content_type == "image/jpeg"
    assert storage.url(name) == "/media/recognitions/2026/10/a.jpg"

    storage.delete(name)
    assert not storage.exists(name)
    with pytest.raises(FileNotFoundError):
        storage.open(name)


def test_name_collision_gets_a_new_name():
    storage = DatabaseStorage()
    first = storage.save("x.jpg", ContentFile(b"1"))
    second = storage.save("x.jpg", ContentFile(b"2"))
    assert first != second
    assert StoredFile.objects.count() == 2


def test_recognition_photo_is_stored_served_and_deleted(
    db_media, client, seeded, client_id, fake_roboflow, django_capture_on_commit_callbacks
):
    fake_roboflow.response = {"predictions": []}
    response = client.post(
        reverse("recognition:recognize"),
        {"image": SimpleUploadedFile("p.jpg", make_image(size=(200, 100)), "image/jpeg")},
        headers={"X-Client-Id": client_id},
    )
    assert response.status_code == 201
    image_url = response.json()["image_url"]
    stored = StoredFile.objects.get()
    assert image_url == f"http://testserver/media/{stored.name}"

    photo = client.get(f"/media/{stored.name}")
    assert photo.status_code == 200
    assert photo["Content-Type"] == "image/jpeg"
    assert photo.content[:2] == b"\xff\xd8"  # JPEG magic
    assert "immutable" in photo["Cache-Control"]
    assert client.get("/media/recognitions/missing.jpg").status_code == 404

    recognition = Recognition.objects.get()
    with django_capture_on_commit_callbacks(execute=True):
        recognition.delete()
    assert not StoredFile.objects.exists()
