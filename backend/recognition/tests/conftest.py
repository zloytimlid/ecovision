import uuid
from io import BytesIO

import pytest
from django.core.management import call_command
from PIL import Image

from catalog.models import ModelClassMapping, WasteCategory


def make_image(size=(64, 48), image_format="JPEG", mode="RGB", color=(200, 30, 30), exif=None):
    image = Image.new(mode, size, color)
    output = BytesIO()
    save_kwargs = {"exif": exif} if exif is not None else {}
    image.save(output, format=image_format, **save_kwargs)
    return output.getvalue()


# Fixed test classes, so the tests do not depend on the classes of the real model.
TEST_CLASS_MAPPINGS = [
    ("plastic_cup", "Пластиковый стаканчик", "plastic"),
    ("plastic_bottle", "Пластиковая бутылка", "plastic"),
    ("paper_cup", "Бумажный стаканчик", "composite"),
    ("tetra_pak", "Тетрапак", "composite"),
    ("glass_jar", "Стеклянная банка", "glass"),
    ("battery", "Батарейка", "batteries"),
    ("phone", "Телефон", "electronics"),
    ("cable", "Кабель", "electronics"),
]


@pytest.fixture
def seeded(db):
    call_command("seed_waste")
    ModelClassMapping.objects.all().delete()
    categories = {c.slug: c for c in WasteCategory.objects.all()}
    ModelClassMapping.objects.bulk_create(
        ModelClassMapping(model_class=cls, display_name=name, category=categories[slug])
        for cls, name, slug in TEST_CLASS_MAPPINGS
    )


@pytest.fixture
def client_id():
    return str(uuid.uuid4())


class FakeRoboflowClient:
    """Stands in for RoboflowClient in API tests: returns a canned response or raises."""

    response = None
    error = None
    calls = []

    def __init__(self, *args, **kwargs):
        pass

    def predict(self, image_bytes):
        FakeRoboflowClient.calls.append(image_bytes)
        if FakeRoboflowClient.error is not None:
            raise FakeRoboflowClient.error
        return FakeRoboflowClient.response


@pytest.fixture
def fake_roboflow(monkeypatch):
    FakeRoboflowClient.response = {"predictions": []}
    FakeRoboflowClient.error = None
    FakeRoboflowClient.calls = []
    monkeypatch.setattr("recognition.views.RoboflowClient", FakeRoboflowClient)
    return FakeRoboflowClient
