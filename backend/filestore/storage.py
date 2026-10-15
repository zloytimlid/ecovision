"""Django storage backend that keeps files in the database (StoredFile)."""

import mimetypes
from urllib.parse import urljoin

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class DatabaseStorage(Storage):
    def _model(self):
        from .models import StoredFile  # avoid importing models at settings load time

        return StoredFile

    def _open(self, name, mode="rb"):
        try:
            stored = self._model().objects.get(name=name)
        except self._model().DoesNotExist:
            raise FileNotFoundError(name) from None
        file = ContentFile(bytes(stored.content), name=name)
        return file

    def _save(self, name, content):
        content.seek(0)
        data = content.read()
        content_type = (
            getattr(content, "content_type", None)
            or mimetypes.guess_type(name)[0]
            or "application/octet-stream"
        )
        self._model().objects.create(name=name, content=data, content_type=content_type, size=len(data))
        return name

    def delete(self, name):
        self._model().objects.filter(name=name).delete()

    def exists(self, name):
        return self._model().objects.filter(name=name).exists()

    def size(self, name):
        try:
            return self._model().objects.values_list("size", flat=True).get(name=name)
        except self._model().DoesNotExist:
            raise FileNotFoundError(name) from None

    def url(self, name):
        return urljoin(settings.MEDIA_URL, name)
