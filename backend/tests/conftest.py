import pytest
from backend.app import app as flask_app

@pytest.fixture
def app():
    yield flask_app 