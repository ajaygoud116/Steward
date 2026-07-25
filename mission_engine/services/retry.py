from enum import Enum
from typing import Dict, Any, Optional


class FailureClass(str, Enum):
    NO_FLIGHTS_FOUND = "NO_FLIGHTS_FOUND"
    NO_HOTELS_FOUND = "NO_HOTELS_FOUND"
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
    INVALID_DATES = "INVALID_DATES"
    INVALID_DESTINATION = "INVALID_DESTINATION"
    TOOL_TIMEOUT = "TOOL_TIMEOUT"
    TOOL_UNAVAILABLE = "TOOL_UNAVAILABLE"
    SCHEMA_ERROR = "SCHEMA_ERROR"


_RETRYABLE: set = {
    FailureClass.NO_FLIGHTS_FOUND,
    FailureClass.NO_HOTELS_FOUND,
    FailureClass.TOOL_TIMEOUT,
}

_NOT_RETRYABLE: set = {
    FailureClass.BUDGET_EXCEEDED,
    FailureClass.INVALID_DATES,
    FailureClass.INVALID_DESTINATION,
    FailureClass.TOOL_UNAVAILABLE,
    FailureClass.SCHEMA_ERROR,
}

_RETRY_DELAYS: dict = {
    FailureClass.NO_FLIGHTS_FOUND: 0,
    FailureClass.NO_HOTELS_FOUND: 0,
    FailureClass.TOOL_TIMEOUT: 30,
}

_MAX_ATTEMPTS: dict = {
    FailureClass.NO_FLIGHTS_FOUND: 3,
    FailureClass.NO_HOTELS_FOUND: 3,
    FailureClass.TOOL_TIMEOUT: 2,
}


class RetryPolicy:
    """Deterministic retry decision engine per failure class."""

    @staticmethod
    def is_retryable(failure_class: FailureClass) -> bool:
        return failure_class in _RETRYABLE

    @staticmethod
    def get_retry_delay(failure_class: FailureClass, attempt: int = 1) -> int:
        base = _RETRY_DELAYS.get(failure_class, 0)
        return base * attempt

    @staticmethod
    def get_max_attempts(failure_class: FailureClass) -> int:
        return _MAX_ATTEMPTS.get(failure_class, 1)

    @staticmethod
    def classify_failure(error_message: str, context: Optional[Dict[str, Any]] = None) -> FailureClass:
        err = error_message.lower()
        ctx = context or {}

        if "flight" in err and ("not found" in err or "no flight" in err or "unavail" in err):
            return FailureClass.NO_FLIGHTS_FOUND

        if "hotel" in err and ("not found" in err or "no hotel" in err or "unavail" in err):
            return FailureClass.NO_HOTELS_FOUND

        if "budget" in err or "exceed" in err or "over budget" in err or "expensive" in err:
            return FailureClass.BUDGET_EXCEEDED

        if "date" in err and ("invalid" in err or "past" in err or "format" in err):
            return FailureClass.INVALID_DATES

        if "destination" in err and ("invalid" in err or "not found" in err or "unknown" in err):
            return FailureClass.INVALID_DESTINATION

        if "timeout" in err or "timed out" in err:
            return FailureClass.TOOL_TIMEOUT

        if "unavail" in err or "down" in err or "service" in err:
            return FailureClass.TOOL_UNAVAILABLE

        if "schema" in err or "validation" in err or "parse" in err:
            return FailureClass.SCHEMA_ERROR

        return FailureClass.TOOL_TIMEOUT
