"""Test case TC-Lodge-03 (SCMS-F-012): validate mandatory complaint fields."""
import pytest

from app.complaints.validation import (MANDATORY_FIELDS, validate_complaint_fields,
                                       validation_error_response)

VALID = {"category": "Sanitation", "description": "Overflowing bin",
         "location": "5th Cross Road"}


def test_valid_data_has_no_errors():
    clean, errors = validate_complaint_fields(VALID)
    assert errors == {}
    assert clean == VALID


@pytest.mark.parametrize("field", list(MANDATORY_FIELDS))
def test_missing_field_is_rejected(field):
    data = {k: v for k, v in VALID.items() if k != field}
    _, errors = validate_complaint_fields(data)
    assert list(errors) == [field]
    assert "required" in errors[field]


@pytest.mark.parametrize("blank", ["", "   ", "\n\t", None])
def test_blank_values_are_rejected(blank):
    _, errors = validate_complaint_fields({**VALID, "description": blank})
    assert "description" in errors


def test_all_missing_reports_every_field():
    _, errors = validate_complaint_fields({})
    assert set(errors) == set(MANDATORY_FIELDS)


def test_none_input_is_handled():
    _, errors = validate_complaint_fields(None)
    assert set(errors) == set(MANDATORY_FIELDS)


def test_whitespace_is_trimmed():
    clean, errors = validate_complaint_fields({**VALID, "category": "  Roads  "})
    assert errors == {}
    assert clean["category"] == "Roads"


def test_non_text_value_is_rejected():
    _, errors = validate_complaint_fields({**VALID, "location": 12345})
    assert "location" in errors


def test_too_long_values_are_rejected():
    _, errors = validate_complaint_fields(
        {**VALID, "category": "x" * 81, "location": "y" * 256})
    assert set(errors) == {"category", "location"}


def test_error_response_is_422_in_uniform_format(app):
    resp, status = validation_error_response({"location": "Location is required."})
    body = resp.get_json()
    assert status == 422
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["details"]["fields"] == {"location": "Location is required."}
