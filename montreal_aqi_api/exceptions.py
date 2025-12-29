class MontrealAQIError(Exception):
    """Base exception for Montreal AQI client."""


class APIServerUnreachable(MontrealAQIError):
    """Montreal open data API is unreachable."""


class APIInvalidResponse(MontrealAQIError):
    """Unexpected response from Montreal open data API."""
