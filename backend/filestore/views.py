from django.http import Http404, HttpResponse
from django.views.decorators.http import require_GET

from .models import StoredFile


@require_GET
def serve(request, path):
    """Serve a file stored in the database at MEDIA_URL/<path>."""
    stored = StoredFile.objects.filter(name=path).only("content", "content_type").first()
    if stored is None:
        raise Http404
    response = HttpResponse(bytes(stored.content), content_type=stored.content_type)
    # File names are unique (recognition UUID), so the content never changes.
    response["Cache-Control"] = "public, max-age=31536000, immutable"
    return response
