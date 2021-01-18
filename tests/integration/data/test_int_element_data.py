import pandas as pd

from footbot.data.element_data import get_bootstrap
from footbot.data.utils import run_query
from footbot.data.utils import write_to_table


def test_get_bootstrap():
    data = get_bootstrap()
    assert "elements" in data
    assert "events" in data
    assert isinstance(data["elements"], list)
    assert isinstance(data["events"], list)


def test_write_element_data_to_table(client):
    element_data_df = run_query(
        "SELECT * FROM `footbot-001.fpl.element_data_1920` ORDER BY element, current_event, datetime LIMIT 100",
        client,
    )

    dataset = "integration_tests"
    table = "element_data"
    write_to_table(dataset, table, element_data_df, client, truncate_table=True)

    written_df = run_query(
        f"SELECT * FROM `footbot-001.{dataset}.{table}` ORDER BY element, current_event, datetime LIMIT 100",
        client,
    )

    pd.testing.assert_frame_equal(element_data_df, written_df)
