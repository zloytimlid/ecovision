import logging
import uuid

from django.conf import settings
from django.db import transaction
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from recognition.client_id import CLIENT_ID_HEADER
from recognition.exceptions import FileTooLargeError, InvalidImageError
from recognition.models import Recognition
from recognition.services.image_utils import InvalidImage

from .avatar import delete_avatar, make_avatar, save_avatar
from .models import get_profile
from .serializers import (
    ChangePasswordSerializer,
    ConfirmPasswordSerializer,
    LoginSerializer,
    RegisterSerializer,
    UpdateUserSerializer,
    UserSerializer,
)

logger = logging.getLogger(__name__)


class AuthRateThrottle(AnonRateThrottle):
    """Per-IP limit for login, registration and password checks (brute-force protection)."""

    scope = "auth"


def claim_device_recognitions(request, user):
    """Attach this device's anonymous recognitions to the account."""
    try:
        client_id = uuid.UUID(request.headers.get(CLIENT_ID_HEADER, "").strip())
    except ValueError:
        return 0
    return Recognition.objects.filter(client_id=client_id, user__isnull=True).update(user=user)


def user_data(request, user):
    return UserSerializer(user, context={"request": request}).data


def auth_response(request, user, status_code=status.HTTP_200_OK):
    claimed = claim_device_recognitions(request, user)
    if claimed:
        logger.info("User %s claimed %d anonymous recognitions", user.pk, claimed)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({"token": token.key, "user": user_data(request, user)}, status=status_code)


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
    """Current user: read, edit username / e-mail, delete the account."""

    permission_classes = [IsAuthenticated]

    def get_throttles(self):
        # Deleting the account checks the password, so limit guessing.
        return [AuthRateThrottle()] if self.request.method == "DELETE" else super().get_throttles()

    def get(self, request):
        data = user_data(request, request.user)
        data["recognitions_count"] = request.user.recognitions.count()
        return Response(data)

    def patch(self, request):
        serializer = UpdateUserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.get(request)

    def delete(self, request):
        serializer = ConfirmPasswordSerializer(data=request.data, context={"user": request.user})
        serializer.is_valid(raise_exception=True)
        logger.info("User %s deleted their account", request.user.pk)
        # Recognitions, feedback, token and profile (with the avatar file) are removed in cascade.
        request.user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AvatarView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        upload = request.FILES.get("avatar")
        if upload is None:
            raise InvalidImageError("Прикрепите изображение в поле avatar.")
        if upload.size > settings.MAX_UPLOAD_BYTES:
            raise FileTooLargeError()
        try:
            content = make_avatar(upload.read())
        except InvalidImage:
            raise InvalidImageError() from None
        save_avatar(get_profile(request.user), content)
        return Response(user_data(request, request.user))

    def delete(self, request):
        delete_avatar(get_profile(request.user))
        return Response(user_data(request, request.user))


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, FormParser]
    throttle_classes = [AuthRateThrottle]

    def post(self, request):
        user = request.user
        serializer = ChangePasswordSerializer(data=request.data, context={"user": user})
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            user.set_password(serializer.validated_data["new_password"])
            user.save(update_fields=["password"])
            # New token: other devices are logged out, this one continues with the new key.
            Token.objects.filter(user=user).delete()
            token = Token.objects.create(user=user)
        return Response({"token": token.key})
