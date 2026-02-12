"""Multiplatform OCR service for card text recognition."""

from __future__ import annotations

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

_SUFFIX_PATTERN = re.compile(
    r"\s*[-–—]?\s*(?:VMAX|VSTAR|GX|EX|ex|V)\s*$",
    re.IGNORECASE,
)


def is_available() -> bool:
    """Return True if an OCR backend is available on this platform."""
    try:
        from jnius import autoclass  # noqa: F401

        return True
    except ImportError:
        pass
    try:
        import easyocr  # noqa: F401

        return True
    except ImportError:
        pass
    try:
        import pytesseract  # noqa: F401

        return True
    except ImportError:
        pass
    return False


def warm_up() -> None:
    """Pre-load the OCR model so the first scan is faster."""
    try:
        import easyocr

        _get_easyocr_reader(easyocr)
    except ImportError:
        pass


def recognize_text_from_file(path: str | Path, rotation: int = 0) -> str:
    """Run OCR on an image file and return the extracted text.

    Uses Google ML Kit on Android, EasyOCR on desktop (pytesseract as fallback).

    Args:
        path: Path to the image file.
        rotation: Extra rotation in degrees (0/90/180/270) to apply before OCR.
    """
    path = str(path)

    # Android: ML Kit text recognition
    try:
        from jnius import autoclass

        return _recognize_mlkit(autoclass, path)
    except ImportError:
        pass

    # Desktop: EasyOCR (preferred – better accuracy on card photos)
    try:
        import easyocr

        return _recognize_easyocr(easyocr, path, rotation)
    except ImportError:
        pass

    # Desktop fallback: pytesseract
    try:
        import pytesseract
        from PIL import Image

        img = Image.open(path)
        img = _apply_rotation(img, rotation)
        return pytesseract.image_to_string(img)
    except ImportError:
        pass

    return ""


_easyocr_reader: object | None = None


def _get_easyocr_reader(easyocr: object) -> object:
    """Return a cached EasyOCR Reader instance (lazy singleton)."""
    global _easyocr_reader  # noqa: PLW0603
    if _easyocr_reader is None:
        _easyocr_reader = easyocr.Reader(["fr", "en"], gpu=False, verbose=False)  # type: ignore[union-attr]
    return _easyocr_reader


def _recognize_easyocr(easyocr: object, path: str, rotation: int = 0) -> str:
    """Perform OCR using EasyOCR."""
    from PIL import Image

    img = Image.open(path)
    img = _apply_rotation(img, rotation)

    import numpy as np

    img_array = np.array(img.convert("RGB"))
    reader = _get_easyocr_reader(easyocr)
    results = reader.readtext(img_array)  # type: ignore[union-attr]

    # Combine detected text lines, sorted top-to-bottom by bounding box y-coordinate
    results.sort(key=lambda r: r[0][0][1])  # type: ignore[index]
    return "\n".join(text for _, text, _ in results)


def _apply_rotation(img: object, rotation: int = 0) -> object:
    """Fix image orientation for OCR.

    Applies an explicit rotation to compensate for webcam orientation
    on desktop. Skips EXIF handling since camera4kivy saves raw textures
    without meaningful EXIF orientation data.
    """
    if rotation:
        img = img.rotate(rotation, expand=True)  # type: ignore[union-attr]
    return img


def _recognize_mlkit(autoclass: object, path: str) -> str:
    """Perform OCR using Google ML Kit via pyjnius.

    Uses the synchronous ``Tasks.await()`` API instead of async listeners,
    since pyjnius cannot implement Java listener interfaces directly.
    Must be called from a background thread (not the Android main thread).
    """
    logger.info("ML Kit OCR: loading classes")
    input_image_cls = autoclass("com.google.mlkit.vision.common.InputImage")  # type: ignore[operator]
    text_recognition_cls = autoclass(  # type: ignore[operator]
        "com.google.mlkit.vision.text.TextRecognition"
    )
    text_options_cls = autoclass(  # type: ignore[operator]
        "com.google.mlkit.vision.text.latin.TextRecognizerOptions"
    )
    bitmap_factory_cls = autoclass("android.graphics.BitmapFactory")  # type: ignore[operator]
    tasks_cls = autoclass("com.google.android.gms.tasks.Tasks")  # type: ignore[operator]
    timeunit_cls = autoclass("java.util.concurrent.TimeUnit")  # type: ignore[operator]

    logger.info("ML Kit OCR: decoding bitmap from %s", path)
    bitmap = bitmap_factory_cls.decodeFile(path)
    if bitmap is None:
        logger.warning("ML Kit OCR: bitmap is None for %s", path)
        return ""

    logger.info("ML Kit OCR: creating InputImage and recognizer")
    image = input_image_cls.fromBitmap(bitmap, 0)
    recognizer = text_recognition_cls.getClient(text_options_cls.Builder().build())

    logger.info("ML Kit OCR: calling recognizer.process()")
    task = recognizer.process(image)
    # Tasks.await() blocks until the task completes (must not be on main thread)
    tasks_await = getattr(tasks_cls, "await")  # 'await' is a Python keyword
    logger.info("ML Kit OCR: waiting for result (timeout 15s)")
    result = tasks_await(task, 15, timeunit_cls.SECONDS)
    text = str(result.getText()) if result else ""
    logger.info("ML Kit OCR: result text=%r", text[:100] if text else "")
    return text


def extract_pokemon_name(text: str) -> str | None:
    """Extract a Pokémon name from OCR text using simple heuristics.

    Looks for the first non-empty, non-numeric line and strips common
    suffixes like EX, GX, VMAX, VSTAR, V, ex.
    """
    candidates = extract_pokemon_candidates(text)
    return candidates[0] if candidates else None


def extract_pokemon_candidates(text: str) -> list[str]:
    """Extract all possible Pokémon names from OCR text.

    Returns every non-empty, non-numeric line after stripping known
    suffixes (EX, GX, VMAX, VSTAR, V, ex).  The first entry is the
    most likely card name (topmost line).
    """
    if not text or not text.strip():
        return []

    candidates: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Skip lines that are purely numeric (HP, damage, etc.)
        if re.fullmatch(r"[\d\s.,%/+-]+", line):
            continue
        # Strip known suffixes
        name = _SUFFIX_PATTERN.sub("", line).strip()
        if name and name not in candidates:
            candidates.append(name)

    return candidates
