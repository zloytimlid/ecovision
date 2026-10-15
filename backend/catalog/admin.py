from django import forms
from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html

from .models import ModelClassMapping, WasteCategory, normalize_class_name


class LinesField(forms.CharField):
    """Edits a JSON list of strings as a textarea with one item per line."""

    def __init__(self, **kwargs):
        kwargs.setdefault("required", False)
        kwargs.setdefault("widget", forms.Textarea(attrs={"rows": 4, "cols": 60}))
        kwargs.setdefault("help_text", "Один пункт на строку.")
        super().__init__(**kwargs)

    def prepare_value(self, value):
        if isinstance(value, list):
            return "\n".join(value)
        return value

    def to_python(self, value):
        value = super().to_python(value)
        return [line.strip() for line in value.splitlines() if line.strip()]


class WasteCategoryForm(forms.ModelForm):
    preparation_steps = LinesField(label="Как подготовить")
    do_not = LinesField(label="Что нельзя")
    examples = LinesField(label="Примеры предметов")

    class Meta:
        model = WasteCategory
        fields = "__all__"
        widgets = {"bin_color": forms.TextInput(attrs={"type": "color"})}


class ModelClassMappingForm(forms.ModelForm):
    class Meta:
        model = ModelClassMapping
        fields = "__all__"

    def clean_model_class(self):
        # Normalize here too, so duplicates within one inline formset are caught.
        return normalize_class_name(self.cleaned_data["model_class"])


class ModelClassMappingInline(admin.TabularInline):
    model = ModelClassMapping
    form = ModelClassMappingForm
    extra = 1


def color_swatch(color):
    return format_html(
        '<span style="display:inline-block;width:14px;height:14px;border-radius:3px;'
        'border:1px solid #0003;vertical-align:middle;background:{}"></span> {}',
        color,
        color,
    )


@admin.register(WasteCategory)
class WasteCategoryAdmin(admin.ModelAdmin):
    form = WasteCategoryForm
    inlines = [ModelClassMappingInline]
    list_display = (
        "icon",
        "name",
        "slug",
        "bin_color_display",
        "is_hazardous",
        "mapping_count",
        "sort_order",
    )
    list_display_links = ("icon", "name")
    list_editable = ("sort_order",)
    list_filter = ("is_hazardous",)
    search_fields = ("name", "slug", "description")
    fieldsets = (
        (None, {"fields": ("slug", "name", "icon", "description", "sort_order")}),
        ("Куда выбрасывать", {"fields": ("bin_name", "bin_color", "is_hazardous")}),
        ("Инструкция", {"fields": ("preparation_steps", "do_not", "examples")}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_mapping_count=Count("class_mappings"))

    @admin.display(description="Цвет", ordering="bin_color")
    def bin_color_display(self, obj):
        return color_swatch(obj.bin_color)

    @admin.display(description="Классов модели", ordering="_mapping_count")
    def mapping_count(self, obj):
        return obj._mapping_count


@admin.register(ModelClassMapping)
class ModelClassMappingAdmin(admin.ModelAdmin):
    form = ModelClassMappingForm
    list_display = ("model_class", "display_name", "category")
    list_filter = ("category",)
    list_select_related = ("category",)
    search_fields = ("model_class", "display_name")
