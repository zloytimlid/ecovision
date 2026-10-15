import logging
import uuid

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from recognition.client_id import CLIENT_ID_HEADER
from recognition.models import Recognition

from .serializers import LoginSerializer, RegisterSerializer, UserSerializer

logger = logging.getLogger(__name__)


class AuthRateThrottle(AnonRateThrottle):
    """Per-IP limit for login and registration (brute-force protection)."""

    scope = "auth"


def claim_device_recognitions(request, user):
    """Attach this device's anonymous recognitions to the account."""
    try:
        client_id = uuid.UUID(request.headers.get(CLIENT_ID_HEADER, "").strip())
    except ValueError:
        return 0
    return Recognition.objects.filter(client_id=client_id, user__isnull=True).update(user=user)


def auth_response(request, user, status_code=status.HTTP_200_OK):
    claimed = claim_device_recognitions(request, user)
    if claimed:
        logger.info("User %s claimed %d anonymous recognitions", user.pk, claimed)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({"token": token.key, "user": UserSerializer(user).data}, status=status_code)


class RegisterView(APIView):
    authentication_classes = []
    throttle_classes = [AuthRateThrottle]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return auth_response(request, serializer.save(), status.HTTP_201_CREATED)


class LoginView(APIView):
    authentication_classes = []
    throttle_classes = [AuthRateThrottle]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return auth_response(request, serializer.validated_data["user"])


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # One token per user: logging out ends the session on all devices.
        request.auth.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = UserSerializer(request.user).data
        data["recognitions_count"] = request.user.recognitions.count()
        return Response(data)
