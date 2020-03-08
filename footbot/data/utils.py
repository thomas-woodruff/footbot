import logging
import unidecode as u
import os
from google.cloud import bigquery, tasks_v2, bigquery_storage_v1beta1
from google.protobuf import timestamp_pb2
import datetime
import requests
from six import StringIO


log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_fmt)
logger = logging.getLogger(__name__)


def get_safe_web_name(web_name):
    '''remove accents and casing from web name'''
    try:
        return u.unidecode(web_name).lower()
    except Exception as e:
        logger.info(e)
        return web_name.lower()


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


def set_up_tasks(
        secrets_path='./secrets/service_account.json'
):
    '''set up tasks client'''
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = secrets_path
    return tasks_v2.CloudTasksClient()


def set_up_bigquery(
        secrets_path='./secrets/service_account.json'
):
    '''set up bigquery client'''
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = secrets_path
    return bigquery.Client()


def run_query(
        sql,
        client
):
    '''run bigquery sql and return dataframe'''
    try:
        bqstorage_client = bigquery_storage_v1beta1.BigQueryStorageClient()
        return client.query(sql).to_dataframe(bqstorage_client=bqstorage_client)
    except Exception as e:
        print(e)


def write_to_table(
        dataset,
        table,
        df,
        client,
        write_disposition='WRITE_APPEND'
):
    '''write data to bigquery table'''
    try:
        buf = StringIO()

        dataset_ref = client.dataset(dataset)
        table_ref = dataset_ref.table(table)

        job_config = bigquery.LoadJobConfig()
        job_config.source_format = 'CSV'
        job_config.skip_leading_rows = 1
        job_config.write_disposition = write_disposition

        df.to_csv(buf, index=False)

        buf.seek(0)

        job = client.load_table_from_file(
            buf, table_ref, job_config=job_config)

        return job.result()

    except Exception as e:
        logger.error(e)
        raise e


def create_cloud_task(
        task,
        queue,
        client,
        project='footbot-001',
        location='europe-west2',
        delay=None
):
    parent = client.queue_path(project, location, queue)

    if delay:
        d = datetime.datetime.utcnow() + datetime.timedelta(seconds=delay)
        timestamp = timestamp_pb2.Timestamp()
        timestamp.FromDatetime(d)
        task['schedule_time'] = timestamp

    return client.create_task(parent, task)


def purge_cloud_queue(
        queue,
        client,
        project='footbot-001',
        location='europe-west2'
):
    parent = client.queue_path(project, location, queue)
    return client.purge_queue(parent)


def check_next_event_deadlinetime():
    bootstrap_request = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/')
    events = bootstrap_request.json()['events']

    deadlinetime_str = [i for i in events if i['is_next']][0]['deadline_time']
    deadlinetime = datetime.datetime.strptime(deadlinetime_str, '%Y-%m-%dT%H:%M:%SZ')

    return deadlinetime < datetime.datetime.now() + datetime.timedelta(hours=24)
