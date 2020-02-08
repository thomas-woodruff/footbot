import logging
from footbot.data import utils, element_data, entry_data
from footbot.optimiser import team_selector
from flask import Flask, request


log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_fmt)
logger = logging.getLogger(__name__)


app = Flask(__name__)


def create_update_element_history_fixtures_task(
        element,
        client
):
    logger.info(f'queueing element {element}')

    task = {
        'app_engine_http_request': {
            'http_method': 'POST',
            'relative_uri': f'/update_element_history_fixtures/{element}'
        }
    }

    utils.create_cloud_task(
        task,
        'update-element-history-fixtures',
        client,
        delay=120
    )


def create_update_entry_picks_chips_task(
        entry,
        client
):
    logger.info(f'queueing entry {entry}')

    task = {
        'app_engine_http_request': {
            'http_method': 'POST',
            'relative_uri': f'/update_entry_picks_chips/{entry}'
        }
    }

    utils.create_cloud_task(
        task,
        'update-entry-picks-chips',
        client,
        delay=120
    )


def update_element_history_fixtures_worker(
        element,
        delete=False
):
    logger.info('setting up client')
    client = utils.set_up_bigquery()

    logger.info('getting element gameweek history and fixtures')
    element_history_df, element_fixtures_df = element_data.get_element_history_fixture_dfs(element)

    if delete:
        logger.info('deleting element gameweek history')
        utils.run_query(
            f'DELETE FROM `footbot-001.fpl.element_gameweeks_1920` WHERE element = {element}',
            client
        )

    logger.info('writing element gameweek history')
    utils.write_to_table('fpl',
                         'element_gameweeks_1920',
                         element_history_df,
                         client
                         )
    logger.info('done writing element gameweek history')

    if delete:
        logger.info('deleting element fixtures')
        utils.run_query(
            f'DELETE FROM `footbot-001.fpl.element_future_fixtures_1920` WHERE element = {element}',
            client
        )

    logger.info('writing element fixtures')
    utils.write_to_table('fpl',
                         'element_future_fixtures_1920',
                         element_fixtures_df,
                         client
                         )
    logger.info('done writing element fixtures')


def update_entry_picks_chips_worker(entry, delete=False):
    logger.info('setting up client')
    client = utils.set_up_bigquery()

    logger.info('getting entry data')
    picks_df, chips_df = entry_data.get_top_entry_dfs(entry)

    if delete:
        logger.info('deleting entry picks')
        utils.run_query(
            f'DELETE FROM `footbot-001.fpl.top_entries_picks_1920` WHERE entry = {entry}',
            client
        )
    logger.info('writing entry picks')

    utils.write_to_table('fpl',
                         'top_entries_picks_1920',
                         picks_df,
                         client
                         )
    logger.info('done writing entry picks')

    if delete:
        logger.info('deleting entry chips')
        utils.run_query(
            f'DELETE FROM `footbot-001.fpl.top_entries_chips_1920` WHERE entry = {entry}',
            client
        )

    logger.info('writing entry chips')
    utils.write_to_table('fpl',
                         'top_entries_chips_1920',
                         chips_df,
                         client
                         )
    logger.info('done writing entry chips')


@app.route('/')
def home_route():
    return 'Greetings!'


@app.route('/update_element_data')
def update_element_data_route():
    logger.info('getting element data')
    element_df = element_data.get_element_df()

    client = utils.set_up_bigquery()

    logger.info('writing element data')
    utils.write_to_table('fpl',
                         'element_data_1920',
                         element_df,
                         client
                         )
    logger.info('done writing element data')

    return 'Updated element data, baby'


@app.route('/update_element_history_fixtures')
def update_element_history_fixtures_route():
    logger.info('setting up client')
    tasks_client = utils.set_up_tasks()

    logger.info('purging queue')
    utils.purge_cloud_queue('update-element-history-fixtures', tasks_client )

    elements = element_data.get_elements()

    logger.info('setting up big query client')
    big_query_client = utils.set_up_bigquery()

    logger.info('deleting element gameweek history')
    utils.run_query(
        f'DELETE FROM `footbot-001.fpl.element_gameweeks_1920` WHERE true',
        big_query_client
    )
    logger.info('deleting element fixtures')
    utils.run_query(
        f'DELETE FROM `footbot-001.fpl.element_future_fixtures_1920` WHERE true',
        big_query_client
    )

    logger.info('queueing elements')

    for element in elements:
        create_update_element_history_fixtures_task(element, tasks_client )

    logger.info('elements queued')

    return 'elements queued'


@app.route('/update_element_history_fixtures/<element>', methods=['POST'])
def update_element_history_fixtures_element_route_post(element):
    try:
        update_element_history_fixtures_worker(element)
        return 'lovely stuff'
    except Exception as e:
        logger.error(f'Unable to update element {element} with exception {e}')
        return 'bad news!'


@app.route('/update_element_history_fixtures/<element>', methods=['PUT'])
def update_element_history_fixtures_element_route_put(element):
    try:
        update_element_history_fixtures_worker(element, delete=True)
        return 'lovely stuff'
    except Exception as e:
        logger.error(f'Unable to update element {element} with exception {e}')
        return 'bad news!'


@app.route('/update_entry_picks_chips')
def update_entry_picks_chips_route():
    logger.info('setting up cloud tasks client')
    tasks_client = utils.set_up_tasks()

    logger.info('purging queue')
    utils.purge_cloud_queue('update-entry-picks-chips', tasks_client)

    logger.info('setting up big query client')
    big_query_client = utils.set_up_bigquery()

    logger.info('deleting entry picks history')
    utils.run_query(
        f'DELETE FROM `footbot-001.fpl.top_entries_picks_1920` WHERE true',
        big_query_client
    )
    logger.info('deleting entry chips history')
    utils.run_query(
        f'DELETE FROM `footbot-001.fpl.top_entries_chips_1920` WHERE true',
        big_query_client
    )

    entries = entry_data.get_top_entries()

    logger.info('queueing entries')

    for entry in entries:
        create_update_entry_picks_chips_task(entry, tasks_client)

    logger.info('entries queued')

    return 'entries queued'


@app.route('/update_entry_picks_chips/<entry>', methods=['POST'])
def update_entry_picks_chips_entry_route_post(entry):
    try:
        update_entry_picks_chips_worker(entry)
        return 'lovely stuff'
    except Exception as e:
        logger.error(f'Unable to update entry {entry} with exception {e}')
        return 'bad news!'


@app.route('/update_entry_picks_chips/<entry>', methods=['PUT'])
def update_entry_picks_chips_entry_route_put(entry):
    try:
        update_entry_picks_chips_worker(entry, delete=True)
        return 'lovely stuff'
    except Exception as e:
        logger.error(f'Unable to update entry {entry} with exception {e}')
        return 'bad news!'


@app.route('/optimise_team/<entry>')
def optimise_team_route(entry):
    total_budget = int(request.args.get('total_budget', 1000))
    bench_factor = float(request.args.get('bench_factor', 0.1))
    transfer_penalty = float(request.args.get('transfer_penalty', 4))
    transfer_limit = int(request.args.get('transfer_limit', 15))

    return team_selector.optimise_entry(
        entry,
        total_budget=total_budget,
        bench_factor=bench_factor,
        transfer_penalty=transfer_penalty,
        transfer_limit=transfer_limit
    )


if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='0.0.0.0', port=8022, debug=True)
