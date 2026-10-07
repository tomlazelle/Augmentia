"""Text helpers."""


def word_count(text: str) -> int:
    """Count words separated by runs of whitespace."""
    return len(text.split())


def truncate(text: str, width: int, suffix: str = "…") -> str:
    """Shorten `text` to at most `width` characters, ending with `suffix` when it was cut."""
    if width < len(suffix):
        raise ValueError("width is smaller than the suffix")
    if len(text) <= width:
        return text
    return text[: width - len(suffix)] + suffix
