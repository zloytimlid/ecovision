from django.conf import settings
from rest_framework import serializers

from catalog.models import WasteCategory
from catalog.serializers import WasteCategoryBriefSerializer

from .models import Feedback, Recognition
from .services.postprocess import find_alternatives, load_mapping, normalize


class FeedbackSerializer(serializers.ModelSerializer):
    correct_category = serializers.SlugRelatedField(
        slug_field="slug",
        queryset=WasteCategory.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Feedback
        fields = ("is_correct", "correct_category", "comment", "created_at")
        read_only_fields = ("created_at",)

    def validate(self, attrs):
        if attrs.get("is_correct"):
            attrs["correct_category"] = None
        elif not attrs.get("correct_category"):
            raise serializers.ValidationError(
                {"correct_category": "Укажите правильную категорию, если результат неверный."}
            )
        return attrs


class RecognitionListSerializer(serializers.ModelSerializer):
    """Short form for the history list."""

    image_url = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    feedback = serializers.SerializerMethodField()

    class Meta:
        model = Recognition
        fields = (
            "id",
            "created_at",
            "status",
            "image_url",
            "top_class",
            "top_confidence",
            "category",
            "feedback",
        )

    def get_image_url(self, obj):
        request = self.context.get("request")
        if not obj.image:
            return None
        return request.build_absolute_uri(obj.image.url) if request else obj.image.url

    def get_category(self, obj):
        category = obj.category
        if category is None:
            return None
        return {
            "slug": category.slug,
            "name": category.name,
            "icon": category.icon,
            "bin_color": category.bin_color,
            "is_hazardous": category.is_hazardous,
        }

    def get_feedback(self, obj):
        feedback = getattr(obj, "feedback", None)
        return None if feedback is None else {"is_correct": feedback.is_correct}


class RecognitionSerializer(serializers.ModelSerializer):
    """Full recognition result (POST /recognize/ and GET /recognitions/{id}/)."""

    image_url = serializers.SerializerMethodField()
    image_size = serializers.SerializerMethodField()
    top = serializers.SerializerMethodField()
    objects = serializers.SerializerMethodField()
    alternatives = serializers.SerializerMethodField()
    has_hazardous = serializers.SerializerMethodField()
    feedback = serializers.SerializerMethodField()

    class Meta:
        model = Recognition
        fields = (
            "id",
            "created_at",
            "status",
            "image_url",
            "image_size",
            "top",
            "objects",
            "alternatives",
            "has_hazardous",
            "inference_ms",
            "feedback",
        )

    @property
    def mapping(self):
        if "mapping" not in self.context:
            self.context["mapping"] = load_mapping()
        return self.context["mapping"]

    def get_image_url(self, obj):
        if not obj.image:
            return None
        request = self.context.get("request")
        url = obj.image.url
        return request.build_absolute_uri(url) if request else url

    def get_image_size(self, obj):
        return {"width": obj.image_width, "height": obj.image_height}

    def get_top(self, obj):
        if obj.top_class is None:
            return None
        entry = self.mapping.get(obj.top_class)
        return {
            "model_class": obj.top_class,
            "display_name": entry.display_name if entry else None,
            "confidence": obj.top_confidence,
            "category": WasteCategoryBriefSerializer(obj.category).data if obj.category else None,
        }

    def get_objects(self, obj):
        return [
            {
                "model_class": item.model_class,
                "confidence": item.confidence,
                "bbox": {"x": item.x, "y": item.y, "width": item.width, "height": item.height},
                "category_slug": item.category.slug if item.category else None,
            }
            for item in obj.detected_objects.all()
        ]

    def get_alternatives(self, obj):
        if obj.status == Recognition.Status.NOT_FOUND:
            return []
        predictions = normalize(obj.raw_response, settings.ROBOFLOW_MODEL_TYPE)
        exclude = obj.category.slug if obj.category else None
        return find_alternatives(predictions, self.mapping, exclude_slug=exclude)

    def get_has_hazardous(self, obj):
        categories = [item.category for item in obj.detected_objects.all()]
        categories.append(obj.category)
        return any(category.is_hazardous for category in categories if category)

    def get_feedback(self, obj):
        feedback = getattr(obj, "feedback", None)
        return FeedbackSerializer(feedback).data if feedback else None
