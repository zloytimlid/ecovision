from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "date_joined")


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_username(self, value):
        value = value.strip()
        for validator in User._meta.get_field("username").validators:
            try:
                validator(value)
            except DjangoValidationError as exc:
                raise serializers.ValidationError(list(exc.messages)) from None
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Это имя пользователя уже занято.")
        return value

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
