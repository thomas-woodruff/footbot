import requests
import pandas as pd
import unidecode as u
import statsmodels.api as sm


def get_bootstrap_static_data():
    '''get all data from master endpoint'''
    bootstrap_static_request = requests.get('https://fantasy.premierleague.com/drf/bootstrap-static')
    return bootstrap_static_request.json()


def get_safe_web_name(web_name):
    '''remove accents and casing from web name'''
    return u.unidecode(web_name).lower()


def get_element_gameweek_arr(element_id_arr):
    element_gameweek_arr = []
    for element_id in element_id_arr:
        url = f'https://fantasy.premierleague.com/drf/element-summary/{element_id}'
        element_history = requests.get(url).json()['history']
        element_gameweek_arr.extend(element_history)
    return element_gameweek_arr


def get_fixtures_df():
    fixtures_request = requests.get('https://fantasy.premierleague.com/drf/fixtures/')
    fixtures_data = fixtures_request.json()
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


def get_element_arr(bootstrap_static_data, cols=['id', 'element_type', 'web_name', 'team']):
    return [{k: i[k] for k in cols}
    for i in bootstrap_static_data['elements']]


def get_element_df(cols):
    bootstrap_static_data = get_bootstrap_static_data()
    element_arr = get_element_arr(bootstrap_static_data, cols)
    element_df = pd.DataFrame(element_arr)
    element_df['safe_web_name'] = element_df['web_name'].apply(get_safe_web_name)

    return element_df


def get_element_gameweek_df():
    bootstrap_static_data = get_bootstrap_static_data()

    fixtures_df = get_fixtures_df()
    
    element_arr = get_element_arr(bootstrap_static_data)

    element_id_arr = [i['id'] for i in element_arr]

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

    # calculate own team
    element_gameweek_df['own_team'] = \
        element_gameweek_df.apply(calculate_own_team, axis=1)

    # calculate opposition team
    element_gameweek_df['opposition_team'] = \
        element_gameweek_df.apply(calculate_opposition_team, axis=1)


    return element_gameweek_df


def add_categorical_variables(df, col_name):
    cat_df = pd.get_dummies(df[col_name], prefix=col_name, drop_first=True)
    return df.join(cat_df)


def add_interaction_terms(df, col_name, interaction_col):
    cat_df = pd.get_dummies(df[col_name], prefix=col_name+'_'+interaction_col, drop_first=True)
    interaction_df = cat_df.multiply(df[interaction_col], axis="index")
    return df.join(interaction_df)


def add_home_categorical_variable(df):
    df['was_home'] = df['was_home'].apply(lambda x: int(x == True))


def remove_redundant_columns(df, redundant_cols):
    cols = list(df.columns)
    
    for i in redundant_cols:
        try:
            cols.remove(i)
        except:
            continue

    return df[cols]


def get_response_explanatory_dfs(df, response_variable):
    explanatory_variables = list(df.columns)
    explanatory_variables.remove(response_variable)

    response_df = df[response_variable]
    explanatory_df = sm.add_constant(df[explanatory_variables])

    return (response_df, explanatory_df)


def filter_gameweek_element_df(gameweek_element_df, current_event, element_types, threshold_minutes):
    return element_gameweek_df[
    (element_gameweek_df['event'] <= current_event)
    & (element_gameweek_df['element_type'].isin(element_types))
    & (element_gameweek_df['minutes'] >= threshold_minutes)]


def get_element_gameweek_rolling_df(rolling_cols):
    element_gameweek_df = get_element_gameweek_df()

    element_gameweek_df['row_id'] = element_gameweek_df['row_id'].rank()
    element_gameweek_df['element_fixture_rank'] = element_gameweek_df.groupby('element')['row_id'].rank()

    rolling_df = \
    element_gameweek_df.copy().groupby('element', as_index=True)[['minutes'] + rolling_cols]\
    .rolling(38, min_periods=1).sum().reset_index()[['element', 'minutes'] + rolling_cols]

    rolling_df['element_fixture_rank'] = rolling_df.groupby('element')['minutes'].rank()
    rolling_df['element_fixture_rank'] = rolling_df['element_fixture_rank'] + 1

    element_gameweek_df =\
    element_gameweek_df.join(
        rolling_df.set_index(['element', 'element_fixture_rank']),
        on=['element', 'element_fixture_rank'],
        rsuffix='_rolling')

    for i in rolling_cols:
        element_gameweek_df[i + '_per_minute_rolling'] = \
        element_gameweek_df[i + '_rolling'] / element_gameweek_df['minutes_rolling']
