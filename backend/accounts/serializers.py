from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

User = get_user_model()


def validate_username_value(value, exclude_user=None):
    """Django's username rules plus case-insensitive uniqueness."""
    value = value.strip()
    for validator in User._meta.get_field("username").validators:
        try:
            validator(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from None
    taken = User.objects.filter(username__iexact=value)
    if exclude_user is not None:
        taken = taken.exclude(pk=exclude_user.pk)
    if taken.exists():
        raise serializers.ValidationError("Это имя пользователя уже занято.")
    return value


class UserSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "username", "email", "date_joined", "avatar_url")

    def get_avatar_url(self, user):
        profile = getattr(user, "profile", None)
        if profile is None or not profile.avatar:
            return None
        request = self.context.get("request")
        url = profile.avatar.url
        return request.build_absolute_uri(url) if request else url


class UpdateUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ("username", "email")
        extra_kwargs = {"username": {"required": False, "validators": []}}

    def validate_username(self, value):
        return validate_username_value(value, exclude_user=self.instance)


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_current_password(self, value):
        if not self.context["user"].check_password(value):
            raise serializers.ValidationError("Неверный текущий пароль.")
        return value

    def validate_new_password(self, value):
        try:
            validate_password(value, user=self.context["user"])
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from None
        return value


class ConfirmPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_password(self, value):
        if not self.context["user"].check_password(value):
            raise serializers.ValidationError("Неверный пароль.")
        return value


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_username(self, value):
        return validate_username_value(value)

    def validate(self, attrs):
        try:
            validate_password(attrs["password"], user=User(username=attrs["username"]))
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)}) from None
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        # Usernames are unique case-insensitively (see RegisterSerializer), so
        # "Anna" may log in as "anna".
        username = attrs["username"].strip()
        existing = User.objects.filter(username__iexact=username).first()
        user = authenticate(
            request=self.context.get("request"),
            username=existing.username if existing else username,
            password=attrs["password"],
        )
        if user is None:
            raise serializers.ValidationError("Неверное имя пользователя или пароль.")
        attrs["user"] = user
        return attrs
