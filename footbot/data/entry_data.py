import pandas as pd
import requests
from footbot.data import utils


def get_top_entries():
    '''get top entries from bigquery'''
    client = utils.set_up_bigquery()
    sql = 'SELECT * FROM `footbot-001.fpl.top_entries_1920`'

    return list(client.query(sql).to_dataframe()['entry'].values)


def get_top_entries_dfs():
    '''get player picks and chip usage of top entries'''
    entry_season_arr = []

    bootstrap_request = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/')
    bootstrap_data = bootstrap_request.json()

    current_event = [i for i in bootstrap_data['events'] if i['is_current']][0]['id']

    for i in get_top_entries():
        for j in range(1, current_event + 1):
            try:
                entry_season_request = requests.get(f'https://fantasy.premierleague.com/api/entry/{i}/event/{j}/picks/')
                entry_season_data = entry_season_request.json()
                entry_season_data['entry'] = i
                entry_season_data['event'] = j
                entry_season_arr.append(entry_season_data)
            except:
                continue

    picks_df = pd.DataFrame(
        [
            utils.update_return_dict(j, ['entry', 'event'], [i['entry'], i['event']])
            for i in entry_season_arr for j in i['picks']
        ])

    picks_df = picks_df[['entry', 'event'] + list(picks_df.columns)[:-2]]

    chips_df = pd.DataFrame([
        utils.get_dict_keys(i, ['entry', 'event', 'active_chip'])
        for i in entry_season_arr
    ])

    return picks_df, chips_df
