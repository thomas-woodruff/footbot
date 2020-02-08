import pandas as pd
import requests
import datetime
from footbot.data import utils


def get_bootstrap():
    return requests.get('https://fantasy.premierleague.com/api/bootstrap-static/').json()


def get_element_df():
    '''get contemporaneous element data'''
    bootstrap_data = get_bootstrap()

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

    # this is a hack to deal with Bešić
    # UnicodeEncodeError: 'latin-1' codec can't encode character '\u0161' in position 119806: Body ('š') is not valid Latin-1. Use body.encode('utf-8') if you want to send it encoded in UTF-8.
    element_df = element_df[element_df['element'] != 522]

    return element_df


def get_elements():
    '''get list of all elements'''

    bootstrap_data = get_bootstrap()

    return [i['id'] for i in bootstrap_data['elements']]


def sanitise_element_history_df(element_history_df):
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

    return element_history_df


def sanitise_element_fixtures_df(element_fixtures_df):
    element_fixtures_df = element_fixtures_df[
        ['element']
        + list(element_fixtures_df.columns)[:-1]
        ]

    for i in [
        'kickoff_time'
    ]:
        element_fixtures_df[i] = element_fixtures_df[i].astype('datetime64[ms]')

    return element_fixtures_df


def get_element_history_fixture_dfs(element):
    element_data = requests.get(f'https://fantasy.premierleague.com/api/element-summary/{element}/').json()
    element_history = element_data['history']
    element_fixtures = [utils.update_return_dict(k, ['element'], [element]) for k in element_data['fixtures']]

    element_history_df = sanitise_element_history_df(pd.DataFrame(element_history))
    element_fixtures_df = sanitise_element_fixtures_df(pd.DataFrame(element_fixtures))

    return element_history_df, element_fixtures_df
