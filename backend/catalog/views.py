from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response

from .models import WasteCategory
from .serializers import WasteCategoryDetailSerializer, WasteCategorySerializer


def matches(category, query):
    """Case-insensitive search by name, description, examples and recognized items."""
    texts = [category.name, category.description, *category.examples]
    texts += [m.display_name for m in category.class_mappings.all()]
    return any(query in text.casefold() for text in texts)


class CategoryListView(ListAPIView):
    serializer_class = WasteCategorySerializer
    pagination_class = None
    queryset = WasteCategory.objects.prefetch_related("class_mappings")

    def list(self, request, *args, **kwargs):
        categories = list(self.get_queryset())
        # Filtered in Python: SQLite LIKE is case-insensitive for ASCII only,
        # and the catalog is tiny.
        query = request.query_params.get("search", "").strip().casefold()
        if query:
            categories = [c for c in categories if matches(c, query)]
        return Response(self.get_serializer(categories, many=True).data)


class CategoryDetailView(RetrieveAPIView):
    serializer_class = WasteCategoryDetailSerializer
    queryset = WasteCategory.objects.prefetch_related("class_mappings")
    lookup_field = "slug"
