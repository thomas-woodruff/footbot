import pytest

from footbot.data.utils import set_up_bigquery


@pytest.fixture(scope="session")
def client():
    return set_up_bigquery()
