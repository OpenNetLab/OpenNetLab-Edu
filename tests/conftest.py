import pytest

from OpenNetLab import simpy

@pytest.fixture
def log():
    return []

@pytest.fixture
def env():
    return simpy.Environment()
