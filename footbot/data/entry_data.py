import logging

import pandas as pd
import requests

from footbot.data import utils

log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=log_fmt)


def get_top_entries():
    """get top entries from bigquery"""
    client = utils.set_up_bigquery()
    sql = "SELECT * FROM `footbot-001.fpl.top_entries_1920`"

    return list(client.query(sql).to_dataframe()["entry"].values)


def get_top_entry_dfs(entry):
    logger = logging.getLogger(__name__)

    bootstrap_request = requests.get(
        "https://fantasy.premierleague.com/api/bootstrap-static/"
    )
    bootstrap_data = bootstrap_request.json()

    current_event = [i for i in bootstrap_data["events"] if i["is_current"]][0]["id"]

    entry_season_arr = []
    for event in range(1, current_event + 1):
        try:
            entry_season_request = requests.get(
                f"https://fantasy.premierleague.com/api/entry/{entry}/event/{event}/picks/"
            )
            entry_season_data = entry_season_request.json()
            entry_season_data["entry"] = entry
            entry_season_data["event"] = event
            entry_season_arr.append(entry_season_data)
        except Exception as e:
            logger.error(
                f"Unable to get data for entry {entry} for event {event} with exception {e}"
            )
            continue

    picks_df = pd.DataFrame(
        [
            utils.update_return_dict(j, ["entry", "event"], [i["entry"], i["event"]])
            for i in entry_season_arr
            for j in i["picks"]
        ]
    )

    picks_df = picks_df[["entry", "event"] + list(picks_df.columns)[:-2]]

    chips_df = pd.DataFrame(
        [
            utils.get_dict_keys(i, ["entry", "event", "active_chip"])
            for i in entry_season_arr
        ]
    )

    return picks_df, chips_df
