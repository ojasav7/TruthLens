"""OCR service — extract text from images."""

from pathlib import Path


def extract_text(image_input) -> dict:
    """
    Extract text from an image using OCR.

    Args:
        image_input: PIL Image, file path, or bytes

    Returns:
        {"text": str, "word_count": int, "available": bool}
    """
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        return {"text": "", "word_count": 0, "available": False, "error": "pytesseract not installed"}

    try:
        if isinstance(image_input, (str, Path)):
            img = Image.open(image_input)
        elif isinstance(image_input, Image.Image):
            img = image_input
        else:
            return {"text": "", "word_count": 0, "available": False, "error": "Unsupported input type"}

        text = pytesseract.image_to_string(img)
        text = text.strip()
        word_count = len(text.split()) if text else 0

        return {"text": text, "word_count": word_count, "available": True}
    except Exception as e:
        # Tesseract binary not found or other error
        return {"text": "", "word_count": 0, "available": False, "error": str(e)}
