import uuid

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from catalog.models import WasteCategory
from recognition.models import Feedback, Recognition

pytestmark = pytest.mark.django_db


@pytest.fixture
def category():
    return WasteCategory.objects.create(
        slug="plastic", name="Пластик", bin_name="Контейнер «Пластик»", bin_color="#F5C400"
    )


@pytest.fixture
def recognition(category):
    return Recognition.objects.create(
        client_id=uuid.uuid4(),
        image=SimpleUploadedFile("photo.jpg", b"fake-jpeg", content_type="image/jpeg"),
        image_width=10,
        image_height=10,
        status=Recognition.Status.OK,
        top_class="plastic_cup",
        top_confidence=0.9,
        category=category,
    )


def test_deleting_recognition_removes_photo(recognition, django_capture_on_commit_callbacks):
    storage, name = recognition.image.storage, recognition.image.name
    assert name.startswith("recognitions/")
    assert storage.exists(name)

    with django_capture_on_commit_callbacks(execute=True):
        recognition.delete()

    assert not storage.exists(name)


def test_negative_feedback_requires_correct_category(recognition, category):
    feedback = Feedback(recognition=recognition, is_correct=False)
    with pytest.raises(ValidationError) as exc:
        feedback.full_clean()
    assert "correct_category" in exc.value.message_dict

    feedback.correct_category = category
    feedback.full_clean()
