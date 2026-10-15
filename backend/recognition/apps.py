from django.apps import AppConfig


class RecognitionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "recognition"
    verbose_name = "Распознавание"

    def ready(self):
        from . import signals  # noqa: F401
