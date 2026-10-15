from rest_framework.throttling import SimpleRateThrottle

from .client_id import CLIENT_ID_HEADER


class RecognizeRateThrottle(SimpleRateThrottle):
    """Limits recognitions per user, per X-Client-Id, or per IP when neither is known."""

    scope = "recognize"

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            ident = f"user-{request.user.pk}"
        else:
            ident = request.headers.get(CLIENT_ID_HEADER, "").strip()[:64] or self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}
