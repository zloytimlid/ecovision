import uuid

from django.core.exceptions import ValidationError
from django.db import models

from catalog.models import WasteCategory


class Recognition(models.Model):
    class Status(models.TextChoices):
        OK = "ok", "Распознано"
        LOW_CONFIDENCE = "low_confidence", "Низкая уверенность"
        NOT_FOUND = "not_found", "Предмет не найден"
        UNMAPPED_CLASS = "unmapped_class", "Нет правил для класса"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client_id = models.UUIDField("ID устройства", db_index=True)
    image = models.ImageField("Фото", upload_to="recognitions/%Y/%m/")
    image_width = models.PositiveIntegerField("Ширина, px")
    image_height = models.PositiveIntegerField("Высота, px")
    status = models.CharField("Статус", max_length=20, choices=Status.choices)
    top_class = models.CharField("Класс модели", max_length=100, null=True, blank=True)
    top_confidence = models.FloatField("Уверенность", null=True, blank=True)
    category = models.ForeignKey(
        WasteCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recognitions",
        verbose_name="Категория",
    )
    raw_response = models.JSONField("Ответ Roboflow", default=dict, blank=True)
    inference_ms = models.PositiveIntegerField("Время инференса, мс", default=0)
    created_at = models.DateTimeField("Создано", auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Распознавание"
        verbose_name_plural = "Распознавания"

    def __str__(self):
        label = self.category.name if self.category else self.get_status_display()
        return f"{label} ({self.created_at:%d.%m.%Y %H:%M})" if self.created_at else label


class DetectedObject(models.Model):
    """A single object found on the photo (object-detection models only)."""

    # related_name="objects" (as in the spec) would shadow Recognition.objects,
    # the default manager; the API still exposes these under the "objects" key.
    recognition = models.ForeignKey(
        Recognition,
        on_delete=models.CASCADE,
        related_name="detected_objects",
        verbose_name="Распознавание",
    )
    model_class = models.CharField("Класс модели", max_length=100)
    confidence = models.FloatField("Уверенность")
    # Bounding box center and size in pixels, as returned by Roboflow.
    x = models.FloatField()
    y = models.FloatField()
    width = models.FloatField()
    height = models.FloatField()
    category = models.ForeignKey(
        WasteCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="Категория",
    )

    class Meta:
        ordering = ["-confidence"]
        verbose_name = "Найденный объект"
        verbose_name_plural = "Найденные объекты"

    def __str__(self):
        return f"{self.model_class} ({self.confidence:.0%})"


class Feedback(models.Model):
    recognition = models.OneToOneField(
        Recognition,
        on_delete=models.CASCADE,
        related_name="feedback",
        verbose_name="Распознавание",
    )
    is_correct = models.BooleanField("Результат верный")
    correct_category = models.ForeignKey(
        WasteCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="Правильная категория",
    )
    comment = models.TextField("Комментарий", blank=True)
    # Updated on every save: a repeated rating overwrites the previous one.
    created_at = models.DateTimeField("Дата оценки", auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Обратная связь"
        verbose_name_plural = "Обратная связь"

    def __str__(self):
        return "Верно" if self.is_correct else "Неверно"

    def clean(self):
        if not self.is_correct and self.correct_category_id is None:
            raise ValidationError(
                {"correct_category": "Укажите правильную категорию, если результат неверный."}
            )
