import unidecode as u
import os
from google.cloud import bigquery
import datetime
import time


def get_safe_web_name(web_name):
    '''remove accents and casing from web name'''
    return u.unidecode(web_name).lower()


def update_return_dict(d, k, v):
    '''update and return a dictionary'''
    d[k] = v
    return d


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
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = secrets_path
        client = bigquery.Client()

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
