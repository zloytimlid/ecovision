from io import BytesIO

import pytest
from PIL import Image

from recognition.services.image_utils import InvalidImage, process_image

from .conftest import make_image

EXIF_ORIENTATION = 0x0112
EXIF_GPS_IFD = 0x8825


def open_result(processed):
    return Image.open(BytesIO(processed.content))


def test_large_image_is_downscaled_to_1280():
    processed = process_image(make_image(size=(4000, 3000)))
    assert (processed.width, processed.height) == (1280, 960)
    with open_result(processed) as image:
        assert image.format == "JPEG"
        assert image.size == (1280, 960)


def test_small_image_is_not_upscaled():
    processed = process_image(make_image(size=(300, 200)))
    assert (processed.width, processed.height) == (300, 200)


def test_exif_orientation_is_applied_and_metadata_removed():
    exif = Image.Exif()
    exif[EXIF_ORIENTATION] = 6  # rotated 90° clockwise
    exif[EXIF_GPS_IFD] = {1: "N", 2: (55.0, 45.0, 0.0)}
    processed = process_image(make_image(size=(200, 100), exif=exif))

    assert (processed.width, processed.height) == (100, 200)
    with open_result(processed) as image:
        assert not image.getexif()
        assert "exif" not in image.info


@pytest.mark.parametrize("image_format", ["PNG", "WEBP"])
def test_png_and_webp_are_converted_to_jpeg(image_format):
    data = make_image(size=(50, 50), image_format=image_format, mode="RGBA", color=(0, 0, 0, 0))
    processed = process_image(data)
    with open_result(processed) as image:
        assert image.format == "JPEG"
        assert image.mode == "RGB"
        # Transparent pixels become white, not black.
        assert image.getpixel((25, 25)) == pytest.approx((255, 255, 255), abs=3)


@pytest.mark.parametrize(
    "data",
    [
        b"",
        b"definitely not an image",
        make_image()[:200],  # truncated JPEG
    ],
    ids=["empty", "text", "truncated"],
)
def test_broken_files_are_rejected(data):
    with pytest.raises(InvalidImage):
        process_image(data)


@pytest.mark.parametrize("image_format", ["GIF", "BMP"])
def test_unsupported_formats_are_rejected(image_format):
    with pytest.raises(InvalidImage):
        process_image(make_image(image_format=image_format))
