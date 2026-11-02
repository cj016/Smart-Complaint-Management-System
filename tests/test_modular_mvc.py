"""SCMS-NF006 / TC-Maint-01: Sample modular architecture test."""

from examples.sample_feedback.models import SampleFeedback
from examples.sample_feedback.routes import bp
from examples.sample_feedback.services import prepare_feedback


def test_sample_model():
    item = SampleFeedback(message="Hello")
    assert item.message == "Hello"


def test_sample_service():
    item = prepare_feedback("  Test feedback  ")
    assert item.message == "Test feedback"


def test_sample_service_rejects_empty_message():
    try:
        prepare_feedback("   ")
        assert False, "Expected validation error"
    except ValueError:
        pass


def test_sample_module_can_be_registered(app):
    app.register_blueprint(
        bp,
        url_prefix="/api/v1/sample-feedback",
    )

    client = app.test_client()

    response = client.post(
        "/api/v1/sample-feedback/",
        json={"message": "Sample module works"},
    )

    assert response.status_code == 201
    assert response.get_json() == {
        "message": "Sample module works",
        "status": "accepted",
    }


def test_sample_module_validates_input(app):
    app.register_blueprint(
        bp,
        url_prefix="/api/v1/sample-feedback",
    )

    response = app.test_client().post(
        "/api/v1/sample-feedback/",
        json={"message": ""},
    )

    assert response.status_code == 422
