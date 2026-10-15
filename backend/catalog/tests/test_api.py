import pytest
from django.core.management import call_command
from django.urls import reverse

pytestmark = pytest.mark.django_db

LIST_URL = reverse("catalog:category-list")


@pytest.fixture(autouse=True)
def seeded():
    call_command("seed_waste")


def slugs(response):
    return [c["slug"] for c in response.json()]


def test_list_returns_all_categories_in_order(client):
    response = client.get(LIST_URL)
    assert response.status_code == 200
    assert slugs(response)[0] == "plastic"
    assert len(response.json()) == 10
    assert {"slug", "name", "bin_color", "icon", "examples"} <= set(response.json()[0])


@pytest.mark.parametrize(
    "query, expected",
    [
        ("стекло", ["glass"]),  # name, any case
        ("ГАЗЕТА", ["paper"]),  # example
        ("обувь", ["textile"]),  # name / recognized item
        ("абракадабра", []),
    ],
)
def test_search(client, query, expected):
    assert slugs(client.get(LIST_URL, {"search": query})) == expected


def test_detail_includes_recognized_items(client):
    response = client.get(reverse("catalog:category-detail", args=["paper"]))
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Бумага и картон"
    assert body["items"] == ["Бумага", "Картон"]
    assert body["do_not"]


def test_unknown_category_is_404(client):
    response = client.get(reverse("catalog:category-detail", args=["nope"]))
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
