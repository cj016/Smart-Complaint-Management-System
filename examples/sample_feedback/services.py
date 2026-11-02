"""Service: business rules for the sample module."""

from .models import SampleFeedback


def prepare_feedback(message):
    if not isinstance(message, str) or not message.strip():
        raise ValueError("Message is required.")

    return SampleFeedback(message=message.strip())
