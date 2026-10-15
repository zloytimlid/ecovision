import uuid

from .exceptions import MissingClientIdError

CLIENT_ID_HEADER = "X-Client-Id"


def get_client_id(request):
    """Return the anonymous device ID from the X-Client-Id header as a UUID."""
    try:
        return uuid.UUID(request.headers.get(CLIENT_ID_HEADER, "").strip())
    except ValueError:
        raise MissingClientIdError() from None
