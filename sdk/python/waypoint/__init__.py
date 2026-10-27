"""Python SDK for the fictional Waypoint Rentals API. See examples/sdk-quickstart-python.md."""
from .client import Rental, RentalLine, Waypoint
from .errors import (
    APIConnectionError,
    APIError,
    AuthenticationError,
    ConfigurationError,
    ConflictError,
    NotFoundError,
    PreconditionFailedError,
    ServerError,
    UnprocessableEntityError,
    WaypointError,
)

__version__ = "0.1.0"
