"""Model: data structure for the sample module."""

from dataclasses import dataclass


@dataclass
class SampleFeedback:
    message: str
