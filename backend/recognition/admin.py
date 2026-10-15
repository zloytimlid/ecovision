import json

from django.contrib import admin
from django.utils.html import format_html

from .models import DetectedObject, Feedback, Recognition


def render_image(image, size):
    if not image:
        return "—"
    return format_html(
        '<img src="{}" style="max-width:{}px;max-height:{}px;border-radius:4px">',
        image.url,
        size,
        size,
    )


class DetectedObjectInline(admin.TabularInline):
    model = DetectedObject
    extra = 0
    can_delete = False
    fields = ("model_class", "confidence", "category", "x", "y", "width", "height")
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


class FeedbackInline(admin.StackedInline):
    model = Feedback
    extra = 0
    fields = ("is_correct", "correct_category", "comment", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Recognition)
class RecognitionAdmin(admin.ModelAdmin):
    inlines = [DetectedObjectInline, FeedbackInline]
    list_display = (
        "thumbnail",
        "created_at",
        "user",
        "status",
        "category",
        "top_class",
        "confidence_display",
        "inference_ms",
        "feedback_display",
    )
    list_filter = ("status", "category", "created_at")
    list_select_related = ("category", "feedback", "user")
    search_fields = ("id", "client_id", "top_class", "user__username")
    date_hierarchy = "created_at"
    readonly_fields = (
        "id",
        "client_id",
        "user",
        "image_preview",
        "image",
        "image_width",
        "image_height",
        "status",
        "top_class",
        "top_confidence",
        "category",
        "inference_ms",
        "created_at",
        "raw_response_display",
    )
    fields = readonly_fields

    def has_add_permission(self, request):
        # Records are created only through the recognition API.
        return False

    @admin.display(description="Фото")
    def thumbnail(self, obj):
        return render_image(obj.image, 60)

    @admin.display(description="Превью")
    def image_preview(self, obj):
        return render_image(obj.image, 480)

    @admin.display(description="Уверенность", ordering="top_confidence")
    def confidence_display(self, obj):
        return "—" if obj.top_confidence is None else f"{obj.top_confidence:.0%}"

    @admin.display(description="Оценка")
    def feedback_display(self, obj):
        feedback = getattr(obj, "feedback", None)
        if feedback is None:
            return "—"
        return "✅" if feedback.is_correct else "❌"

    @admin.display(description="Ответ Roboflow")
    def raw_response_display(self, obj):
        return format_html(
            '<pre style="white-space:pre-wrap;max-height:400px;overflow:auto">{}</pre>',
            json.dumps(obj.raw_response, ensure_ascii=False, indent=2),
        )


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = (
        "thumbnail",
        "is_correct",
        "predicted_category",
        "correct_category",
        "comment",
        "created_at",
    )
    list_filter = ("is_correct", "correct_category", "created_at")
    list_select_related = ("recognition__category", "correct_category")
    search_fields = ("comment", "recognition__top_class")
    raw_id_fields = ("recognition",)

    @admin.display(description="Фото")
    def thumbnail(self, obj):
        return render_image(obj.recognition.image, 60)

    @admin.display(description="Предсказано")
    def predicted_category(self, obj):
        return obj.recognition.category or obj.recognition.top_class or "—"
