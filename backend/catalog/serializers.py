from rest_framework import serializers

from .models import WasteCategory


class WasteCategoryBriefSerializer(serializers.ModelSerializer):
    """Category data needed to show a recognition result."""

    class Meta:
        model = WasteCategory
        fields = (
            "slug",
            "name",
            "bin_name",
            "bin_color",
            "icon",
            "preparation_steps",
            "do_not",
            "is_hazardous",
        )


class WasteCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = WasteCategory
        fields = (
            "slug",
            "name",
            "description",
            "bin_name",
            "bin_color",
            "icon",
            "preparation_steps",
            "do_not",
            "examples",
            "is_hazardous",
        )


class WasteCategoryDetailSerializer(WasteCategorySerializer):
    items = serializers.SerializerMethodField()

    class Meta(WasteCategorySerializer.Meta):
        fields = (*WasteCategorySerializer.Meta.fields, "items")

    def get_items(self, obj):
        """Items the model recognizes as this category (from the class mapping)."""
        return sorted({m.display_name for m in obj.class_mappings.all()})
