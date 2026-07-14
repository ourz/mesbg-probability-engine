class MESBGProbabilityError(Exception):
    """Base package exception."""


class ValidationError(MESBGProbabilityError):
    """Raised when a combat specification is incomplete or contradictory."""
