import unidecode as u
import os
from google.cloud import bigquery
import datetime
import time
import requests


def get_safe_web_name(web_name):
    '''remove accents and casing from web name'''
    return u.unidecode(web_name).lower()


def update_return_dict(d, k, v):
    '''update and return a dictionary'''
    if not (isinstance(k, list) and isinstance(v, list) and len(k) == len(v)):
        raise Exception

    for i in range(0, len(k)):
        d[k[i]] = v[i]
    return d


def get_dict_keys(d, k):
    '''filter dictionary for relevant keys'''
    if not (isinstance, k, list):
        raise Exception
    arr = []
    for i in k:
        arr.append((i, d[i]))

    return dict(arr)


def set_up_bigquery(
        secrets_path='./secrets/service_account.json'
):
    '''set up bigquery client'''
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = secrets_path
    return bigquery.Client()


def run_query(
        sql,
        secrets_path='./secrets/service_account.json'
):
    '''run bigquery sql and return dataframe'''
    try:
        client = set_up_bigquery(secrets_path)
        return client.query(sql).to_dataframe()
    except Exception as e:
        print(e)


def write_to_table(
        dataset,
        table,
        df,
        write_disposition='WRITE_APPEND',
        secrets_path='./secrets/service_account.json',
        csvs_path='./csvs/'
):
    '''write data to bigquery table'''
    try:
        client = set_up_bigquery(secrets_path)

        dataset_ref = client.dataset(dataset)
        table_ref = dataset_ref.table(table)

        filename = csvs_path + table + datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        df.to_csv(filename, index=False)

        time.sleep(3)

        with open(filename, 'rb') as source_file:
            job_config = bigquery.LoadJobConfig()
            job_config.skip_leading_rows = 1
            job_config.autodetect = True
            job_config.write_disposition = write_disposition
            client.load_table_from_file(
                source_file, table_ref, job_config=job_config)

        time.sleep(3)
        os.remove(filename)

    except Exception as e:
        print(e)


def check_next_event_deadlinetime(window_hours=24):
    bootstrap_request = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/')
    events = bootstrap_request.json()['events']

    deadlinetime_str = [i for i in events if i['is_next']][0]['deadline_time']
    deadlinetime = datetime.datetime.strptime(deadlinetime_str, '%Y-%m-%dT%H:%M:%SZ')

    return deadlinetime < datetime.datetime.now() + datetime.timedelta(hours=24)
