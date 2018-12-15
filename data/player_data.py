import requests
import pandas as pd
import unidecode as u


def get_bootstrap_static_data():
    '''get all data from master endpoint'''
    bootstrap_static_request = requests.get('https://fantasy.premierleague.com/drf/bootstrap-static')
    return bootstrap_static_request.json()


def get_safe_web_name(web_name):
    '''remove accents and casing from web name'''
    return u.unidecode(web_name).lower()


def get_fixtures_data():
    '''get all data from fixtures endpoint'''
    fixtures_request = requests.get('https://fantasy.premierleague.com/drf/fixtures/')
    return fixtures_request.json()


def get_element_gameweek_arr(element_id_arr):
    element_gameweek_arr = []
    for element_id in element_id_arr:
        url = f'https://fantasy.premierleague.com/drf/element-summary/{element_id}'
        element_history = requests.get(url).json()['history']
        element_gameweek_arr.extend(element_history)
    return element_gameweek_arr


def get_fixtures_df(fixtures_data):
    fixtures_arr = [{
        k: i[k]
        for k in
        ['id', 'team_h', 'team_a', 'team_h_difficulty', 'team_a_difficulty', 'event']
    } for i in fixtures_data]
    return pd.DataFrame(fixtures_arr)


def calculate_own_team(row):
    team_h, team_a, was_home = row[['team_h', 'team_a', 'was_home']]
    if was_home:
        return team_h
    else:
        return team_a


def calculate_opposition_team(row):
    team_h, team_a, was_home = row[['team_h', 'team_a', 'was_home']]
    if was_home:
        return team_a
    else:
        return team_h


# # calculate rolling season average data
# season_avg_df = element_gameweek_df.groupby('element')[['total_points', 'goals_scored']] \
#     .rolling(38, min_periods=1).mean().reset_index('element')

# season_avg_df = season_avg_df.join(element_gameweek_df['round'])

# season_avg_df['round'] = element_gameweek_df['round'] + 1
# season_avg_df.rename(
#     columns={
#         'total_points': 'season_avg_total_points',
#         'goals_scored': 'season_avg_goals_scored'
#     },
#     inplace=True)


def get_element_df():
    bootstrap_static_data = get_bootstrap_static_data()
    fixtures_data = get_fixtures_data()

    fixtures_df = get_fixtures_df(fixtures_data)
    
    element_arr = [{k: i[k] for k in 
    ['id', 'element_type', 'web_name', 'team']}
    for i in bootstrap_static_data['elements']]

    element_id_arr = [i['id'] for i in element_arr][0:10]

    element_df = pd.DataFrame(element_arr)

    # get web name without accents and casing
    element_df['safe_web_name'] = element_df['web_name'].apply(get_safe_web_name)

    element_gameweek_arr = get_element_gameweek_arr(element_id_arr)
    element_gameweek_df = pd.DataFrame(element_gameweek_arr)

    # join fixture data on player gameweek data
    element_gameweek_df = element_gameweek_df.join(fixtures_df.set_index('id'), on='fixture')

    # join player data on player gameweek data
    element_gameweek_df = element_gameweek_df.join(element_df.set_index('id'), on='element')

    element_gameweek_df.index.name = 'row_id'

    return element_gameweek_df

# # calculate own team
# element_gameweek_df['own_team'] = \
#     element_gameweek_df.apply(calculate_own_team, axis=1)

# # calculate opposition team
# element_gameweek_df['opposition_team'] = \
#     element_gameweek_df.apply(calculate_opposition_team, axis=1)






# element_gameweek_df = \
#     element_gameweek_df.set_index(['element', 'round']) \
#         .join(season_avg_df.set_index(['element', 'round'])).reset_index()

# element_gameweek_df.index.name = 'row_id'


