import pytest

from OpenNetLab import sim

@pytest.fixture
def log():
    return []

@pytest.fixture
def env():
    return sim.Environment()
