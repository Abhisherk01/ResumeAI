# tests/conftest.py
import os

# Must be set BEFORE the app is imported so settings pick them up.
os.environ["DATABASE_URL"] = "sqlite://"  # in-memory SQLite for tests
os.environ["ENVIRONMENT"] = "test"

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)
