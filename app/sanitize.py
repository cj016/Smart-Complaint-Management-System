import re

_TAGS = re.compile(r"<[^>]*>")
_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def clean_text(value, max_len=None):
    """Strip HTML tags and control characters from free text.
    Output is still escaped on display (textContent / Jinja autoescape)."""
    if value is None:
        return None
    text = _CTRL.sub("", _TAGS.sub("", str(value))).strip()
    return text[:max_len] if max_len else text