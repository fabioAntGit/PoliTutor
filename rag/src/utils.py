"""
File Management and Utilities Module.

Provides utilities for extracting metadata from filenames following the project's
naming convention, and for saving base64-encoded images to structured output directories.

Filename convention:
    <source_type>.<course_code>.<description>.<extension>

    Examples:
        apontamentos.ed.cap1.pdf
        slides.pp.aula3.pptx
"""

import re
import logging
import base64
from pathlib import Path
from config import VALID_SOURCE_TYPES
from config import IMAGES_OUTPUT_DIR

logger = logging.getLogger(__name__)

COURSE_CODE_PATTERN = re.compile(r'^[a-z]+$')

def extract_metadata_from_filename(filename: str) -> tuple[str, str, str]:
    """
    Extracts the source type, course code, and stem from a filename.

    Parses the filename stem by splitting on dots. source_type and course_code
    are returned as lowercase.

    Args:
        filename: Full filename including extension (e.g. 'Apontamentos.ED.CAP1.pdf').

    Returns:
        A tuple of (source_type, course_code, stem), where source_type and
        course_code are lowercase and stem preserves the original casing.

    Raises:
        ValueError: If the filename has fewer than two dot-separated parts, or if
                    course_code contains non-alphabetic characters.
    """
    stem = Path(filename).stem
    parts = stem.split(".")

    if len(parts) < 2:
        raise ValueError(
            f"Filename '{filename}' does not follow the expected format "
            f"'<source_type>.<course_code>.<description>.[pdf,pptx,md...]'."
        )

    source_type = parts[0].lower()
    course_code = parts[1].lower()

    if source_type not in VALID_SOURCE_TYPES:
        logger.warning(
            f"Unknown source_type '{source_type}' in '{filename}'. "
            f"Expected one of: {VALID_SOURCE_TYPES}."
        )

    if not COURSE_CODE_PATTERN.match(course_code):
        raise ValueError(
            f"course_code '{course_code}' in '{filename}' contains invalid characters."
        )

    return source_type, course_code, stem

def save_image(image_b64: str, source_filename: str, page_num: int, img_index: int) -> str:
    """
    Decodes a base64 image and saves it to the structured output directory.

    The output path is derived from the source filename metadata:
        IMAGES_OUTPUT_DIR/<course_code>/<source_type>/<stem>/p<page>_img<index>.png

    If metadata extraction fails, falls back to
        IMAGES_OUTPUT_DIR/unknown/unknown/<stem>/... to avoid data loss.

    Args:
        image_b64:       Base64-encoded image string.
        source_filename: Original document filename (used to derive the output path).
        page_num:        Page number where the image was found.
        img_index:       Index of the image within that page.

    Returns:
        Absolute path to the saved image file.
    """
    try:
        source_type, course_code, stem = extract_metadata_from_filename(source_filename)
    except ValueError as e:
        logger.warning("Saving image to fallback directory due to metadata error: %s", e)
        course_code = "unknown"
        source_type = "unknown"
        stem = Path(source_filename).stem

    image_dir = IMAGES_OUTPUT_DIR / course_code / source_type / stem
    image_dir.mkdir(parents=True, exist_ok=True)

    image_path = image_dir / f"p{page_num}_img{img_index}.png"
    with open(image_path, "wb") as f:
        f.write(base64.b64decode(image_b64))

    return str(image_path)