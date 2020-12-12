import os
from pathlib import Path

import pytest

from footbot.data.utils import set_up_bigquery
from footbot.research.utils.simulator import get_element_data


@pytest.fixture
def client():
    secrets_path = os.path.join(
        Path(__file__).parents[4], "secrets/service_account.json"
    )
    return set_up_bigquery(secrets_path)


def test_get_element_data(client):
    df = get_element_data("1920", 15, client)
    columns = set(df.columns)
    expected_columns = {"element_all", "element_type", "team", "value"}

    assert columns == expected_columns
    assert len(df) == 586
    assert len(df["element_all"]) == len(df["element_all"].drop_duplicates())
