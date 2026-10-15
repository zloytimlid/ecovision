import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def isolated_media_root(settings, tmp_path):
    """Keep uploaded test files out of backend/media."""
    settings.MEDIA_ROOT = tmp_path / "media"


@pytest.fixture(autouse=True)
def clear_throttle_cache():
    cache.clear()
