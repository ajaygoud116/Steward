from mission_engine.services.retry import RetryPolicy, FailureClass


class TestFailureClassification:
    def test_classify_no_flights_found(self):
        fc = RetryPolicy.classify_failure("No flights found for the requested route")
        assert fc == FailureClass.NO_FLIGHTS_FOUND

    def test_classify_no_hotels_found(self):
        fc = RetryPolicy.classify_failure("No hotels available in the area")
        assert fc == FailureClass.NO_HOTELS_FOUND

    def test_classify_budget_exceeded(self):
        fc = RetryPolicy.classify_failure("The total cost exceeds your budget")
        assert fc == FailureClass.BUDGET_EXCEEDED

    def test_classify_invalid_dates(self):
        fc = RetryPolicy.classify_failure("The departure date format is invalid")
        assert fc == FailureClass.INVALID_DATES

    def test_classify_invalid_destination(self):
        fc = RetryPolicy.classify_failure("Destination not found in our system")
        assert fc == FailureClass.INVALID_DESTINATION

    def test_classify_tool_timeout(self):
        fc = RetryPolicy.classify_failure("flight_search timed out after 30 seconds")
        assert fc == FailureClass.TOOL_TIMEOUT

    def test_classify_tool_unavailable(self):
        fc = RetryPolicy.classify_failure("The flight booking service is down")
        assert fc == FailureClass.TOOL_UNAVAILABLE

    def test_classify_schema_error(self):
        fc = RetryPolicy.classify_failure("Schema validation failed for tool output")
        assert fc == FailureClass.SCHEMA_ERROR

    def test_classify_fallback_default(self):
        fc = RetryPolicy.classify_failure("Something unexpected happened")
        assert fc == FailureClass.TOOL_TIMEOUT


class TestRetryability:
    def test_no_flights_found_is_retryable(self):
        assert RetryPolicy.is_retryable(FailureClass.NO_FLIGHTS_FOUND)

    def test_no_hotels_found_is_retryable(self):
        assert RetryPolicy.is_retryable(FailureClass.NO_HOTELS_FOUND)

    def test_tool_timeout_is_retryable(self):
        assert RetryPolicy.is_retryable(FailureClass.TOOL_TIMEOUT)

    def test_budget_exceeded_not_retryable(self):
        assert not RetryPolicy.is_retryable(FailureClass.BUDGET_EXCEEDED)

    def test_invalid_dates_not_retryable(self):
        assert not RetryPolicy.is_retryable(FailureClass.INVALID_DATES)

    def test_invalid_destination_not_retryable(self):
        assert not RetryPolicy.is_retryable(FailureClass.INVALID_DESTINATION)

    def test_tool_unavailable_not_retryable(self):
        assert not RetryPolicy.is_retryable(FailureClass.TOOL_UNAVAILABLE)

    def test_schema_error_not_retryable(self):
        assert not RetryPolicy.is_retryable(FailureClass.SCHEMA_ERROR)


class TestRetryConfig:
    def test_get_max_attempts(self):
        assert RetryPolicy.get_max_attempts(FailureClass.NO_FLIGHTS_FOUND) == 3
        assert RetryPolicy.get_max_attempts(FailureClass.TOOL_TIMEOUT) == 2
        assert RetryPolicy.get_max_attempts(FailureClass.BUDGET_EXCEEDED) == 1

    def test_get_retry_delay(self):
        delay = RetryPolicy.get_retry_delay(FailureClass.TOOL_TIMEOUT, attempt=2)
        assert delay == 60
