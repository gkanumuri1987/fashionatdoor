"""Image normalization for uploads (palm, Vastu).

Phones produce 3-48MB photos in JPEG/HEIC/WebP/PNG; the vision model wants a
reasonably-sized JPEG. Every uploaded image is normalized here:
- decoded with Pillow (HEIC/HEIF via pillow-heif when installed),
- EXIF-rotated upright (phone photos are usually stored rotated),
- downscaled to a max edge of 2048px,
- re-encoded as JPEG (quality 88).

Returns None only when the bytes are not a decodable image — the caller then
gives the user a CLEAR format message instead of a silent drop.
"""

from __future__ import annotations

import io
import logging

logger = logging.getLogger("imaging")

MAX_UPLOAD_BYTES = 30 * 1024 * 1024   # explicit refusal above this, never silent
MAX_EDGE = 2048
JPEG_QUALITY = 88

_HEIF_REGISTERED = False


def _ensure_heif() -> None:
    global _HEIF_REGISTERED
    if _HEIF_REGISTERED:
        return
    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
    except ImportError:  # pragma: no cover — HEIC support is best-effort
        logger.info("pillow-heif not installed — HEIC uploads will not decode")
    _HEIF_REGISTERED = True


def normalize_image(raw: bytes) -> bytes | None:
    """Any decodable image → upright, ≤2048px, RGB JPEG bytes. None if not an image."""
    _ensure_heif()
    try:
        from PIL import Image, ImageOps
        img = Image.open(io.BytesIO(raw))
        img.load()
        img = ImageOps.exif_transpose(img)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        elif img.mode == "L":
            img = img.convert("RGB")
        w, h = img.size
        edge = max(w, h)
        if edge > MAX_EDGE:
            scale = MAX_EDGE / edge
            img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))),
                             Image.LANCZOS)
        out = io.BytesIO()
        img.save(out, "JPEG", quality=JPEG_QUALITY)
        return out.getvalue()
    except Exception as exc:
        logger.warning("image normalization failed: %s", exc)
        return None
