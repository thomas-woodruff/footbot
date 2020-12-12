import os
from pathlib import Path

from footbot.data.utils import run_templated_query
from footbot.data.utils import set_up_bigquery


def get_element_data(season, event, client):

    sql_template_path = os.path.join(Path(__file__).parents[0], "element_data.sql")

    df = run_templated_query(
        sql_template_path, dict(season=season, event=event), client
    )

    return df


def get_results_data(season, event, client):

    sql_template_path = os.path.join(Path(__file__).parents[0], "results_data.sql")

    df = run_templated_query(
        sql_template_path, dict(season=season, event=event), client
    )

    return df
