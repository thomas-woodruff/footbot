import os
from pathlib import Path

import pytest

from footbot.data.utils import set_up_bigquery
from footbot.research.utils.simulator import get_element_data
from footbot.research.utils.simulator import get_results_data


@pytest.fixture
def client():
    secrets_path = os.path.join(
        Path(__file__).parents[4], "secrets/service_account.json"
    )
    return set_up_bigquery(secrets_path)


def test_get_element_data(client):
    df = get_element_data("1920", 15, client)

    assert set(df.columns) == {"element_all", "element_type", "team", "value"}
    assert len(df) == 586
    assert len(df["element_all"]) == len(df["element_all"].drop_duplicates())


def test_get_results_data(client):
    df = get_results_data("1920", 15, client)

    assert set(df.columns) == {"element_all", "element_type", "minutes", "total_points"}
    assert len(df) == 564
    assert len(df["element_all"]) == len(df["element_all"].drop_duplicates())
