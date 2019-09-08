import pandas as pd
import requests
import datetime
from footbot.data import utils


def get_element_df():
    '''get contemporaneous element data'''
    bootstrap_request = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/')
    bootstrap_data = bootstrap_request.json()

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

    return element_df


def get_element_summary_data():
    '''Loop through element summaries'''
    bootstrap_request = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/')
    bootstrap_data = bootstrap_request.json()

    max_element = max([i['id'] for i in bootstrap_data['elements']])

    element_history_arr = []
    element_fixtures_arr = []
    element_history_past_arr = []

    for i in range(1, max_element + 1):
        try:
            element_request = requests.get(f'https://fantasy.premierleague.com/api/element-summary/{i}/')
            element_data = element_request.json()

            element_history_arr.extend(element_data['history'])

            element_fixtures_arr.extend(
                [utils.update_return_dict(k, 'element', i) for k in element_data['fixtures']])

            element_history_past_arr.extend(
                [utils.update_return_dict(k, 'element', i) for k in element_data['history_past']])
        except:
            continue

    return element_history_arr, element_fixtures_arr, element_history_past_arr


def get_element_summary_dfs():
    '''get element gameweek and future fixture data'''
    element_history_arr, element_fixtures_arr, _ = get_element_summary_data()

    element_history_df = pd.DataFrame(element_history_arr)
    element_history_df.columns = ['event' if i == 'round' else i for i in element_history_df.columns]

    element_fixtures_df = pd.DataFrame(element_fixtures_arr)
    element_fixtures_df = element_fixtures_df[
        ['element']
        + list(element_fixtures_df.columns)[:-1]
        ]

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
