from django.conf import settings
from django.db import models


class Profile(models.Model):
    """Extra user data that the built-in User model does not have."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="Пользователь",
    )
    avatar = models.ImageField("Аватар", upload_to="avatars/", blank=True)

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"

    def __str__(self):
        return str(self.user)


def get_profile(user):
    profile, _ = Profile.objects.get_or_create(user=user)
    return profile
