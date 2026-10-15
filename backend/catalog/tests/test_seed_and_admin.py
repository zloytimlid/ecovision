import pytest
from django.core.management import call_command
from django.urls import reverse

from catalog.admin import WasteCategoryForm
from catalog.models import ModelClassMapping, WasteCategory, normalize_class_name

pytestmark = pytest.mark.django_db


@pytest.fixture
def seeded():
    call_command("seed_waste")


def test_seed_creates_categories_and_mappings(seeded):
    assert WasteCategory.objects.count() == 10
    hazardous = set(WasteCategory.objects.filter(is_hazardous=True).values_list("slug", flat=True))
    assert hazardous == {"batteries", "electronics"}
    # Classes of the Roboflow model waste-bd0et/10, normalized.
    mapping = dict(ModelClassMapping.objects.values_list("model_class", "category__slug"))
    assert mapping == {
        "biological": "organic",
        "cardboard": "paper",
        "clothes": "textile",
        "electronics": "electronics",
        "glass": "glass",
        "metal": "metal",
        "paper": "paper",
        "plastic": "plastic",
        "shoes": "textile",
    }


def test_seed_keeps_admin_edits_unless_overwrite(seeded):
    WasteCategory.objects.filter(slug="plastic").update(bin_color="#000000")

    call_command("seed_waste")
    assert WasteCategory.objects.get(slug="plastic").bin_color == "#000000"

    call_command("seed_waste", "--overwrite")
    assert WasteCategory.objects.get(slug="plastic").bin_color == "#F5C400"
    assert WasteCategory.objects.count() == 10


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("plastic_bottle", "plastic_bottle"),
        ("Plastic Bottle", "plastic_bottle"),
        ("  glass-jar ", "glass_jar"),
        ("Tetra - Pak", "tetra_pak"),
    ],
)
def test_normalize_class_name(raw, expected):
    assert normalize_class_name(raw) == expected


def test_mapping_is_saved_normalized(seeded):
    mapping = ModelClassMapping.objects.create(
        model_class="Coffee-Cup Lid",
        display_name="Крышка",
        category=WasteCategory.objects.get(slug="plastic"),
    )
    mapping.refresh_from_db()
    assert mapping.model_class == "coffee_cup_lid"


def test_category_form_edits_lists_line_by_line(seeded):
    category = WasteCategory.objects.get(slug="glass")
    data = {
        field: getattr(category, field)
        for field in ("slug", "name", "description", "bin_name", "bin_color", "icon", "sort_order")
    }
    data.update(
        preparation_steps="Опустошить\n\n  Снять крышки  \n",
        do_not="Зеркала",
        examples="",
        is_hazardous=False,
    )
    form = WasteCategoryForm(data, instance=category)
    assert form.is_valid(), form.errors
    form.save()

    category.refresh_from_db()
    assert category.preparation_steps == ["Опустошить", "Снять крышки"]
    assert category.do_not == ["Зеркала"]
    assert category.examples == []


def test_category_form_rejects_bad_color(seeded):
    category = WasteCategory.objects.get(slug="glass")
    form = WasteCategoryForm({"bin_color": "green"}, instance=category)
    assert not form.is_valid()
    assert "bin_color" in form.errors


@pytest.mark.parametrize(
    "url_name",
    [
        "admin:catalog_wastecategory_changelist",
        "admin:catalog_modelclassmapping_changelist",
        "admin:recognition_recognition_changelist",
        "admin:recognition_feedback_changelist",
    ],
)
def test_admin_changelists_open(seeded, admin_client, url_name):
    assert admin_client.get(reverse(url_name)).status_code == 200


def test_admin_category_page_shows_mapping_inline(seeded, admin_client):
    category = WasteCategory.objects.get(slug="paper")
    response = admin_client.get(reverse("admin:catalog_wastecategory_change", args=[category.pk]))
    assert response.status_code == 200
    assert 'value="cardboard"' in response.content.decode()
