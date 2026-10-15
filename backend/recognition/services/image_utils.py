"""Validation and re-encoding of uploaded photos."""

from dataclasses import dataclass
from io import BytesIO

from PIL import Image, ImageOps

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
MAX_SIDE = 1280
JPEG_QUALITY = 85


class InvalidImage(Exception):
    """The file is not a supported, readable image."""


@dataclass(frozen=True)
class ProcessedImage:
    content: bytes
    width: int
    height: int


def process_image(data):
    """
    Validate an uploaded image and re-encode it for storage and inference:
    apply EXIF orientation, drop all metadata (EXIF may contain geolocation),
    downscale to MAX_SIDE on the long side and save as JPEG.
    """
    try:
        with Image.open(BytesIO(data)) as image:
            image_format = image.format
            image.verify()
    except Exception as exc:  # Pillow raises many different exception types here
        raise InvalidImage(str(exc)) from exc

    if image_format not in ALLOWED_FORMATS:
        raise InvalidImage(f"Unsupported format: {image_format}")

    try:
        # verify() leaves the image unusable, so it has to be reopened.
        with Image.open(BytesIO(data)) as image:
            image = ImageOps.exif_transpose(image)
            image.thumbnail((MAX_SIDE, MAX_SIDE), Image.Resampling.LANCZOS)
            image = _to_rgb(image)
            output = BytesIO()
            # No exif/icc arguments are passed, so the result carries no metadata.
            image.save(output, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    except Exception as exc:
        raise InvalidImage(str(exc)) from exc

    return ProcessedImage(content=output.getvalue(), width=image.width, height=image.height)


def _to_rgb(image):
    has_alpha = image.mode in ("RGBA", "LA") or (
        image.mode == "P" and "transparency" in image.info
    )
    if has_alpha:
        image = image.convert("RGBA")
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.getchannel("A"))
        return background
    if image.mode != "RGB":
        return image.convert("RGB")
    return image
