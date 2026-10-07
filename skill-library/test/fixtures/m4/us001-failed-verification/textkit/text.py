"""Text helpers."""

import re


def truncate(text: str, width: int, suffix: str = "…") -> str:
    """Shorten `text` to at most `width` characters, ending with `suffix` when it was cut."""
    if width < len(suffix):
        raise ValueError("width is smaller than the suffix")
    if len(text) <= width:
        return text
    return text[: width - len(suffix)] + suffix


def slugify(text: str) -> str:
    """Turn `text` into a lowercase, hyphen-separated URL slug, preserving letters and digits."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower())
    return slug
