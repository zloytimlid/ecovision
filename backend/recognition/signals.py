from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import Recognition


@receiver(post_delete, sender=Recognition)
def delete_recognition_image(sender, instance, **kwargs):
    """Remove the photo file once the record deletion is committed."""
    if not instance.image:
        return
    storage, name = instance.image.storage, instance.image.name
    transaction.on_commit(lambda: storage.delete(name))
