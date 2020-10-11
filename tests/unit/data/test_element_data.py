import pytest

from footbot.data.element_data import get_bootstrap
from footbot.data.element_data import get_element_df


@pytest.fixture(scope="session")
def bootstrap_data():
    return get_bootstrap()


def test_get_element_df(bootstrap_data):
    element_df = get_element_df(bootstrap_data)
    assert len(element_df) != 0
    assert "id" not in element_df.columns
