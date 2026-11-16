import pytest
from fastapi.testclient import TestClient

from app.config import config
from app.main import app


@pytest.fixture
def client():
    """Enter TestClient so lifespan starts the equity and FI generators."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_tick_timing():
    config.tick_interval_min = 0.05
    config.tick_interval_max = 0.1
    config.heartbeat_interval_s = 0.2
    yield
    config.tick_interval_min = 0.1
    config.tick_interval_max = 1.0
    config.heartbeat_interval_s = 2.0
