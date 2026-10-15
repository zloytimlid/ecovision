from rest_framework.throttling import SimpleRateThrottle

from .client_id import CLIENT_ID_HEADER


class RecognizeRateThrottle(SimpleRateThrottle):
    """Limits recognitions per X-Client-Id, or per IP when the header is absent."""

    scope = "recognize"

    def get_cache_key(self, request, view):
        ident = request.headers.get(CLIENT_ID_HEADER, "").strip()[:64] or self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}
