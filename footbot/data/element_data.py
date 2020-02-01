from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import requests
import datetime
from footbot.data import utils

# from dogpile.cache import make_region
#
# region = make_region().configure(
#     'dogpile.cache.dbm',
#     expiration_time = 3600,
#     arguments={
#         "filename": "cache.dbm"
#     }
# )


# @region.cache_on_arguments()
def _get_bootstrap():
    return requests.get('https://fantasy.premierleague.com/api/bootstrap-static/').json()


# @region.cache_on_arguments()
def _get_element_json(id):
    return id, requests.get(f'https://fantasy.premierleague.com/api/element-summary/{id}/').json()


def get_element_df():
    '''get contemporaneous element data'''
    bootstrap_data = _get_bootstrap()

    current_event = [i for i in bootstrap_data['events'] if i['is_current']][0]['id']

    current_datetime = datetime.datetime.now()

    element_df = pd.DataFrame(bootstrap_data['elements'])

    element_df['element'] = element_df['id']
    element_df['current_event'] = current_event
    element_df['datetime'] = current_datetime
    element_df['safe_web_name'] = element_df['web_name'].apply(utils.get_safe_web_name)

    element_df = element_df[[
        'element', 'current_event', 'datetime', 'safe_web_name', 'assists', 'bonus', 'bps',
        'chance_of_playing_next_round', 'chance_of_playing_this_round',
        'clean_sheets', 'code', 'cost_change_event', 'cost_change_event_fall',
        'cost_change_start', 'cost_change_start_fall', 'creativity',
        'dreamteam_count', 'element_type', 'ep_next', 'ep_this', 'event_points',
        'first_name', 'form', 'goals_conceded', 'goals_scored', 'ict_index',
        'in_dreamteam', 'influence', 'minutes', 'news', 'news_added', 'now_cost',
        'own_goals', 'penalties_missed', 'penalties_saved', 'photo',
        'points_per_game', 'red_cards', 'saves', 'second_name',
        'selected_by_percent', 'special', 'squad_number', 'status', 'team',
        'team_code', 'threat', 'total_points', 'transfers_in',
        'transfers_in_event', 'transfers_out', 'transfers_out_event', 'value_form',
        'value_season', 'web_name', 'yellow_cards'
    ]]

    # sanitise data types
    for i in [
        'creativity',
        'ep_next',
        'ep_this',
        'form',
        'ict_index',
        'influence',
        'points_per_game',
        'selected_by_percent',
        'threat',
        'value_form',
        'value_season'
    ]:
        element_df[i] = element_df[i].astype('float')

    for i in [
        'datetime',
        'news_added'
    ]:
        element_df[i] = element_df[i].astype('datetime64[ms]')

    return element_df


def get_element_summary_data():
    '''Loop through element summaries'''
    bootstrap_data = _get_bootstrap()

    max_element = max([i['id'] for i in bootstrap_data['elements']])

    element_history_arr = []
    element_fixtures_arr = []
    element_history_past_arr = []

    with ThreadPoolExecutor(max_workers=25) as executor:
        results = executor.map(_get_element_json, range(1, max_element + 1))

    for i, element_data in results:
        try:

            element_history_arr.extend(element_data['history'])

            element_fixtures_arr.extend(
                [utils.update_return_dict(k, ['element'], [i]) for k in element_data['fixtures']])

            element_history_past_arr.extend(
                [utils.update_return_dict(k, ['element'], [i]) for k in element_data['history_past']])
        except Exception as e:
            print(e)
            continue

    return element_history_arr, element_fixtures_arr, element_history_past_arr


def get_element_summary_dfs():
    '''get element gameweek and future fixture data'''
    element_history_arr, element_fixtures_arr, _ = get_element_summary_data()
    element_history_df = pd.DataFrame(element_history_arr)
    element_history_df.columns = ['event' if i == 'round' else i for i in element_history_df.columns]

    # sanitise data types
    for i in [
        'creativity',
        'ict_index',
        'influence',
        'threat',
    ]:
        element_history_df[i] = element_history_df[i].astype('float')

    for i in [
        'kickoff_time'
    ]:
        element_history_df[i] = element_history_df[i].astype('datetime64[ms]')

    element_fixtures_df = pd.DataFrame(element_fixtures_arr)
    element_fixtures_df = element_fixtures_df[
        ['element']
        + list(element_fixtures_df.columns)[:-1]
        ]

    for i in [
        'kickoff_time'
    ]:
        element_fixtures_df[i] = element_fixtures_df[i].astype('datetime64[ms]')

    return element_history_df, element_fixtures_df


def get_element_past_history_df():
    '''get element past season data'''
    _, _, element_history_past_arr = get_element_summary_data()

    element_history_past_df = pd.DataFrame(element_history_past_arr)
    element_history_past_df = element_history_past_df[
        ['element']
        + list(element_history_past_df.columns)[:-1]
        ]

    return element_history_past_df
