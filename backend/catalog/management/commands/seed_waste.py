from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import ModelClassMapping, WasteCategory, normalize_class_name
from catalog.seed_data import CATEGORIES, CLASS_MAPPINGS


class Command(BaseCommand):
    help = (
        "Load the initial waste categories and model class mapping. "
        "Existing records are kept as is unless --overwrite is given."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Replace existing records with the seed values (discards admin edits).",
        )

    @transaction.atomic
    def handle(self, *args, overwrite=False, **options):
        stats = {"created": 0, "updated": 0, "skipped": 0}

        categories = {}
        for order, data in enumerate(CATEGORIES, start=1):
            defaults = {**data, "sort_order": order * 10}
            slug = defaults.pop("slug")
            category, outcome = self._upsert(WasteCategory, {"slug": slug}, defaults, overwrite)
            categories[slug] = category
            stats[outcome] += 1

        for model_class, display_name, slug in CLASS_MAPPINGS:
            _, outcome = self._upsert(
                ModelClassMapping,
                {"model_class": normalize_class_name(model_class)},
                {"display_name": display_name, "category": categories[slug]},
                overwrite,
            )
            stats[outcome] += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Категорий: {WasteCategory.objects.count()}, "
                f"классов модели: {ModelClassMapping.objects.count()} "
                f"(создано {stats['created']}, обновлено {stats['updated']}, "
                f"без изменений {stats['skipped']})."
            )
        )

    @staticmethod
    def _upsert(model, lookup, defaults, overwrite):
        if overwrite:
            obj, created = model.objects.update_or_create(**lookup, defaults=defaults)
            return obj, "created" if created else "updated"
        obj, created = model.objects.get_or_create(**lookup, defaults=defaults)
        return obj, "created" if created else "skipped"
