"""Avatar images: validated, cropped to a square and stored without metadata."""

import uuid
from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image, ImageOps

from recognition.services.image_utils import process_image

AVATAR_SIZE = 256


def make_avatar(data):
    """
    Return a square JPEG avatar. Raises image_utils.InvalidImage for files that
    are not JPEG/PNG/WEBP images. EXIF (incl. geolocation) is dropped.
    """
    # Reuses the photo pipeline: format check, EXIF orientation, metadata removal.
    processed = process_image(data)
    with Image.open(BytesIO(processed.content)) as image:
        square = ImageOps.fit(image, (AVATAR_SIZE, AVATAR_SIZE), Image.Resampling.LANCZOS)
        output = BytesIO()
        square.save(output, format="JPEG", quality=88, optimize=True)
    return output.getvalue()


def save_avatar(profile, content):
    """Replace the profile avatar; the old file is removed."""
    old = profile.avatar.name if profile.avatar else None
    # A new name every time: avatar URLs are cached as immutable.
    profile.avatar.save(f"{profile.user_id}-{uuid.uuid4().hex[:8]}.jpg", ContentFile(content), save=True)
    if old:
        profile.avatar.storage.delete(old)


def delete_avatar(profile):
    if profile.avatar:
        profile.avatar.delete(save=True)
