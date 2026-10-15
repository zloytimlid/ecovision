from django.db import models


class StoredFile(models.Model):
    """Uploaded file kept in the database (used where the server has no persistent disk)."""

    name = models.CharField("Путь", max_length=255, unique=True)
    content = models.BinaryField("Содержимое")
    content_type = models.CharField("Тип", max_length=100, default="application/octet-stream")
    size = models.PositiveIntegerField("Размер, байт")
    created_at = models.DateTimeField("Загружен", auto_now_add=True)

    class Meta:
        verbose_name = "Файл"
        verbose_name_plural = "Файлы"

    def __str__(self):
        return self.name
