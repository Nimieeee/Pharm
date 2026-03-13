# Multi-Provider AI Routing - Testing Infrastructure

## Overview

This document describes the testing infrastructure set up for the Multi-Provider AI Routing Strategy implementation.

## Test Structure

The testing infrastructure is organized into three main test files:

### 1. `test_multi_provider_unit.py`
Contains unit tests for individual components and methods in isolation:
- Provider initialization and configuration
- Mode-to-model mapping
- Priority-based routing
- Rate limit handling
- RPM tracking
- Weighted distribution
- Error tracking and recovery
- Streaming and non-streaming generation
- Thread safety
- Capacity reporting
- Scale targets
- Request format compatibility
- Singleton management

### 2. `test_multi_provider_properties.py`
Contains property-based tests using Hypothesis to verify correctness properties across a wide range of inputs:
- All tests run with minimum 100 iterations as specified in the design
- Uses `@settings(max_examples=100)` decorator
- Tests universal properties that should hold for all valid inputs
- Covers all 41 correctness properties from the design document

### 3. `test_multi_provider_integration.py`
Contains end-to-end integration tests:
- Successful request flow scenarios
- Provider failover scenarios
- Exhaustive failure handling
- Concurrent request handling
- Rate limit recovery
- Error recovery
- Weighted distribution verification
- Mode-specific routing validation

## Mock Infrastructure

### Mock Response Classes

#### `MockSSEResponse`
Simulates Server-Sent Events (SSE) streaming responses:
- Configurable content chunks
- Configurable HTTP status codes (200, 429, 500, etc.)
- Optional [DONE] marker
- Proper SSE format with "data: " prefix
- JSON structure matching OpenAI API format

#### `MockJSONResponse`
Simulates non-streaming JSON responses:
- Configurable content
- Configurable HTTP status codes
- JSON structure matching OpenAI API format
- Proper choices[0].message.content structure

### Fixtures

#### Provider Configuration Fixtures
- `mock_nvidia_config`: NVIDIA provider configuration
- `mock_groq_config`: Groq provider configuration
- `mock_mistral_config`: Mistral provider configuration

#### Response Fixtures
- `mock_sse_success_response`: Successful SSE streaming response
- `mock_sse_rate_limit_response`: 429 rate limit error response
- `mock_sse_server_error_response`: 500 server error response
- `mock_json_success_response`: Successful JSON response
- `mock_json_rate_limit_response`: 429 rate limit error response
- `mock_json_server_error_response`: 500 server error response

#### Environment Fixtures
- `mock_environment_variables`: Sets up test API keys
- `mock_empty_environment`: Removes all API keys for testing error handling

#### HTTP Client Fixtures
- `mock_httpx_client`: Mock httpx.AsyncClient for HTTP request mocking

### Helper Functions

#### `create_mock_http_response()`
Creates mock HTTP responses with configurable parameters:
- Content and status code
- Streaming vs non-streaming
- Content chunks for streaming

#### `create_malformed_sse_response()`
Creates malformed SSE responses for testing error handling:
- Invalid JSON
- Missing content fields
- Empty choices array

## Dependencies

The following testing dependencies have been installed:

```
pytest>=7.4.0           # Testing framework
pytest-asyncio>=0.21.0  # Async test support
hypothesis>=6.82.0      # Property-based testing
pytest-httpx>=0.21.0    # HTTP mocking for pytest
httpx>=0.24.0          # HTTP client library
```

## Running Tests

### Run all tests
```bash
pytest backend/tests/test_multi_provider_*.py -v
```

### Run unit tests only
```bash
pytest backend/tests/test_multi_provider_unit.py -v
```

### Run property tests only
```bash
pytest backend/tests/test_multi_provider_properties.py -v --hypothesis-seed=random
```

### Run integration tests only
```bash
pytest backend/tests/test_multi_provider_integration.py -v
```

### Run with coverage
```bash
pytest backend/tests/test_multi_provider_*.py --cov=app.services.multi_provider --cov-report=html
```

## Verification

The mock infrastructure has been verified with `test_mock_infrastructure.py`, which tests:
- SSE response generation
- JSON response generation
- Error status handling
- Provider configuration fixtures
- Environment variable mocking
- Helper function behavior

All 10 verification tests pass successfully.

## Next Steps

The testing infrastructure is now ready for implementing the actual multi-provider tests in subsequent tasks:
- Task 2: Provider configuration and initialization tests
- Task 3: Mode-specific model mapping tests
- Task 4: Priority-based routing tests
- And so on...

Each subsequent task will add tests to the appropriate test file (unit, properties, or integration) using the mock infrastructure provided here.
