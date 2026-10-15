from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import Profile


@receiver(post_delete, sender=Profile)
def delete_avatar_file(sender, instance, **kwargs):
    """Remove the avatar file when the profile (or the whole account) is deleted."""
    if not instance.avatar:
        return
    storage, name = instance.avatar.storage, instance.avatar.name
    transaction.on_commit(lambda: storage.delete(name))
