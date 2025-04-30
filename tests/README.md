# Tests for IoT Edge Device Management Platform

This directory contains tests for the IoT Edge Device Management Platform.

## Structure

```
tests/
├── conftest.py                  # Shared pytest fixtures and configuration
├── test_db.py                   # Database setup for testing
├── test_utils.py                # Utility functions for testing
├── pytest.ini                   # Pytest configuration
├── api/
│   ├── test_auth.py             # Authentication route tests
│   ├── test_users.py            # User route tests
│   └── test_customers.py        # Customer route tests
└── utils/
    ├── test_audit.py            # Audit logging tests
    └── test_email.py            # Email functionality tests
```

## Setting Up

1. Initialize the environment

```bash
pipenv shell
```

## Running Tests

### Run all tests:

```bash
python -m pytest -v --capture=no --disable-warnings
```


### Run a specific test file:

```bash
python -m pytest tests/api/test_auth.py
```

### Run a specific test function:

```bash
python -m pytest -s --disable-warnings tests/api/test_auth.py::test_login_success
```
