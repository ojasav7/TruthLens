"""EXIF metadata analysis — check image metadata for manipulation signs."""

from pathlib import Path


def analyze_metadata(image_input) -> dict:
    """
    Analyze image EXIF metadata for manipulation indicators.

    Checks:
    - Missing/stripped metadata (common in edited images)
    - Camera make/model present
    - GPS coordinates present
    - Software tags (Photoshop, GIMP, etc.)

    Returns:
        {
            "has_exif": bool,
            "suspicious": bool,
            "signals": list[str],
            "metadata": dict
        }
    """
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS
    except ImportError:
        return {"has_exif": False, "suspicious": False, "signals": ["Pillow not installed"], "metadata": {}}

    try:
        if isinstance(image_input, (str, Path)):
            img = Image.open(image_input)
        elif isinstance(image_input, Image.Image):
            img = image_input
        else:
            return {"has_exif": False, "suspicious": False, "signals": ["Unsupported input"], "metadata": {}}

        exif_data = img.getexif()
        signals = []
        metadata = {}

        if not exif_data:
            return {
                "has_exif": False,
                "suspicious": True,
                "signals": ["No EXIF data found — metadata may have been stripped"],
                "metadata": {},
            }

        # Extract key tags
        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)
            if isinstance(value, bytes):
                value = value[:50]  # truncate long byte values
            metadata[str(tag)] = str(value)[:100]

        # Check for editing software
        software = metadata.get("Software", "").lower()
        editing_tools = ["photoshop", "gimp", "lightroom", "snapseed", "vsco", "afterlight"]
        if any(t in software for t in editing_tools):
            signals.append(f"Editing software detected: {metadata.get('Software')}")

        # Check for camera info and GPS
        make = metadata.get("Make", "")
        model = metadata.get("Model", "")
        has_gps = any("GPS" in k for k in metadata)
        if not make and not model:
            signals.append("No camera make/model -- possible synthetic image")
        if not has_gps:
            signals.append("No GPS data")

        suspicious = len(signals) >= 2 or (not make and not model and len(exif_data) < 5)

        return {
            "has_exif": True,
            "suspicious": suspicious,
            "signals": signals if signals else ["Metadata appears normal"],
            "metadata": metadata,
        }
    except Exception as e:
        return {"has_exif": False, "suspicious": False, "signals": [f"Error: {e}"], "metadata": {}}
