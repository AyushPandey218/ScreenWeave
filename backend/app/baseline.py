"""Geometry-only feasibility baseline; not a semantic UI detector or OCR engine."""

from io import BytesIO

import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError

MAX_BYTES = 5 * 1024 * 1024
MAX_PIXELS = 4_000_000


def inspect_image(payload: bytes) -> dict:
    if not payload or len(payload) > MAX_BYTES:
        raise ValueError("Image must contain between 1 byte and 5 MiB.")
    try:
        with Image.open(BytesIO(payload)) as source:
            if source.format not in {"PNG", "JPEG"}:
                raise ValueError("Only PNG and JPEG images are supported.")
            if source.width * source.height > MAX_PIXELS:
                raise ValueError("Image exceeds the 4 megapixel limit.")
            source.load()
            rgb = np.asarray(source.convert("RGB"))
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError("Invalid or unsafe image.") from exc
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 60, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    regions = []
    for contour in contours:
        x, y, width, height = cv2.boundingRect(contour)
        if width >= 40 and height >= 20:
            regions.append({"x": x, "y": y, "width": width, "height": height})
    return {
        "width": rgb.shape[1],
        "height": rgb.shape[0],
        "regions": sorted(regions, key=lambda box: (box["y"], box["x"])),
        "method": "external-contour-baseline",
        "limitations": "No text extraction, semantic labels, or nested-container detection.",
    }
