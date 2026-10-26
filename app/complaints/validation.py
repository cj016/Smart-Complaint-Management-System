"""Server-side validation for complaint submissions (SCMS-F-012).

The citizen form also checks these fields in the browser, but the server must
check them again because the browser check can be bypassed.
"""
from ..errors import error_response

# field name -> maximum length (matches the columns in app/models/complaint.py)
MANDATORY_FIELDS = {
    "category": 80,
    "description": None,  # Text column, no length limit
    "location": 255,
}


def validate_complaint_fields(data):
    """Check category, description and location.

    Returns (clean, errors):
      clean  - the three fields with surrounding whitespace removed
      errors - {field: message}; empty when everything is valid
    """
    data = data or {}
    clean, errors = {}, {}

    for field, max_len in MANDATORY_FIELDS.items():
        value = data.get(field)
        if value is not None and not isinstance(value, str):
            errors[field] = f"{field.capitalize()} must be text."
            continue
        value = (value or "").strip()
        if not value:
            errors[field] = f"{field.capitalize()} is required."
        elif max_len and len(value) > max_len:
            errors[field] = f"{field.capitalize()} must be at most {max_len} characters."
        else:
            clean[field] = value

    return clean, errors


def validation_error_response(errors):
    """422 Unprocessable Entity in the uniform error format (SAD 4.3 / 4.4)."""
    return error_response(
        "VALIDATION_ERROR",
        "Some required fields are missing or invalid.",
        {"fields": errors},
        422,
    )
