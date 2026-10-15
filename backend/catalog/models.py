import re

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

hex_color_validator = RegexValidator(
    regex=r"^#[0-9A-Fa-f]{6}$",
    message="Цвет должен быть в формате HEX, например #F5C400.",
)


def normalize_class_name(value):
    """Normalize a model class name: lowercase, spaces and hyphens become '_'."""
    return re.sub(r"[\s\-]+", "_", (value or "").strip().lower())


def validate_string_list(value):
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValidationError("Ожидается список строк.")


class WasteCategory(models.Model):
    slug = models.SlugField("Slug", unique=True)
    name = models.CharField("Название", max_length=100)
    description = models.TextField("Описание", blank=True)
    bin_name = models.CharField("Куда выбрасывать", max_length=150)
    bin_color = models.CharField(
        "Цвет контейнера", max_length=7, validators=[hex_color_validator]
    )
    icon = models.CharField("Иконка (эмодзи)", max_length=10, blank=True)
    preparation_steps = models.JSONField(
        "Как подготовить", default=list, blank=True, validators=[validate_string_list]
    )
    do_not = models.JSONField(
        "Что нельзя", default=list, blank=True, validators=[validate_string_list]
    )
    examples = models.JSONField(
        "Примеры предметов", default=list, blank=True, validators=[validate_string_list]
    )
    is_hazardous = models.BooleanField("Опасный отход", default=False)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "Категория отходов"
        verbose_name_plural = "Категории отходов"

    def __str__(self):
        return self.name


class ModelClassMapping(models.Model):
    model_class = models.CharField(
        "Класс модели",
        max_length=100,
        unique=True,
        help_text="Как в Roboflow. Регистр не важен, пробелы и дефисы заменяются на «_».",
    )
    display_name = models.CharField("Название предмета", max_length=100)
    category = models.ForeignKey(
        WasteCategory,
        on_delete=models.CASCADE,
        related_name="class_mappings",
        verbose_name="Категория",
    )

    class Meta:
        ordering = ["model_class"]
        verbose_name = "Класс модели"
        verbose_name_plural = "Маппинг классов модели"

    def __str__(self):
        return f"{self.model_class} → {self.category.slug}"

    def clean(self):
        # Runs before validate_unique(), so uniqueness is checked on the normalized value.
        self.model_class = normalize_class_name(self.model_class)

    def save(self, *args, **kwargs):
        self.model_class = normalize_class_name(self.model_class)
        super().save(*args, **kwargs)
