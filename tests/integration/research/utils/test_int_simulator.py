import os
from pathlib import Path

import pytest

from footbot.data.utils import set_up_bigquery
from footbot.research.utils.simulator import get_elements_df
from footbot.research.utils.simulator import get_results_df


@pytest.fixture
def client():
    secrets_path = os.path.join(
        Path(__file__).parents[4], "secrets/service_account.json"
    )
    return set_up_bigquery(secrets_path)


def test_get_element_data(client):
    df = get_elements_df("1920", 15, client)

    assert set(df.columns) == {"element_all", "element_type", "team", "value"}
    assert len(df) == 586
    assert len(df["element_all"]) == len(df["element_all"].drop_duplicates())


def test_get_results_data(client):
    df = get_results_df("1920", 15, client)

    assert set(df.columns) == {"element_all", "minutes", "total_points"}
    assert len(df) == 564
    assert len(df["element_all"]) == len(df["element_all"].drop_duplicates())
