import pytest
import main

@pytest.fixture
def app():
    return main.app
