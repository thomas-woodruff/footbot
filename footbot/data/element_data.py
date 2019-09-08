import pandas as pd
import requests
import datetime
from footbot.data.utils import get_safe_web_name
import os
from google.cloud import bigquery
import time


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
    element_df['safe_web_name'] = element_df['web_name'].apply(get_safe_web_name)

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


def write_to_table():
    '''write element data to bigquery table'''
    try:
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './secrets/service_account.json'
        client = bigquery.Client()

        dataset_ref = client.dataset('fpl')
        table_ref = dataset_ref.table('element_data')

        df = get_element_df()

        filename = './csvs/element_data_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        df.to_csv(filename, index=False)

        time.sleep(10)

        with open(filename, 'rb') as source_file:
            job_config = bigquery.LoadJobConfig()
            job_config.skip_leading_rows = 1
            client.load_table_from_file(
                source_file, table_ref, job_config=job_config)

        time.sleep(10)
        os.remove(filename)
    except Exception as e:
        print(e)
