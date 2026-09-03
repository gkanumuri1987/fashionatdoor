"""Upload image normalization tests."""

import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image

from imaging import MAX_EDGE, normalize_image


def _bytes(img: Image.Image, fmt: str) -> bytes:
    b = io.BytesIO()
    img.save(b, fmt)
    return b.getvalue()


def test_jpeg_passthrough_and_downscale():
    big = Image.new("RGB", (6000, 4000), (200, 150, 120))
    out = normalize_image(_bytes(big, "JPEG"))
    assert out is not None
    w, h = Image.open(io.BytesIO(out)).size
    assert max(w, h) == MAX_EDGE and Image.open(io.BytesIO(out)).format == "JPEG"


def test_png_and_rgba_convert():
    rgba = Image.new("RGBA", (500, 500), (10, 20, 30, 128))
    out = normalize_image(_bytes(rgba, "PNG"))
    assert out is not None
    assert Image.open(io.BytesIO(out)).mode == "RGB"


def test_webp_supported():
    img = Image.new("RGB", (300, 300), (5, 5, 5))
    out = normalize_image(_bytes(img, "WEBP"))
    assert out is not None


def test_exif_rotation_applied():
    img = Image.new("RGB", (400, 200), (1, 2, 3))
    b = io.BytesIO()
    exif = Image.Exif()
    exif[274] = 6  # rotate 90 CW
    img.save(b, "JPEG", exif=exif)
    out = normalize_image(b.getvalue())
    w, h = Image.open(io.BytesIO(out)).size
    assert (w, h) == (200, 400)  # upright after transpose


def test_garbage_returns_none():
    assert normalize_image(b"this is not an image at all") is None
    assert normalize_image(b"") is None
