"""
File Management and Utilities Module.

Provides robust utilities for extracting metadata from filenames based on the project's
internal naming conventions, saving base64 images to the correct output directories, 
and managing API calls with exponential backoff.

Filename Convention Supported: 
    <source_type>.<course_code>.<description>.<extension>
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
    Extracts the source type, course code, and filename stem from a given filename.

    Args:
        filename (str): The full filename or path (e.g., "Slides.ED.CAP1.pdf").

    Returns:
        tuple[str, str, str]: A tuple containing (source_type, course_code, stem), 
            all converted to lowercase (except stem).

    Raises:
        ValueError: If the filename does not contain at least two parts separated by dots,
            or if the course code contains invalid characters.
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
    Decodes a base64 string and saves the image to the appropriate output directory.
    
    The directory is determined by extracting metadata from the `source_filename`. If
    metadata extraction fails, falls back to an 'unknown' directory structure but 
    preserves the file stem to avoid data loss.

    Args:
        image_b64 (str): The base64 encoded image string.
        source_filename (str): The original document filename where the image was found.
        page_num (int): The page number containing the image.
        img_index (int): A unique index for the image on that page.

    Returns:
        str: The absolute path to the newly saved image file.
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