import logging
from footbot.data import utils, element_data, entry_data
from footbot.optimiser import team_selector
from flask import Flask, request
from concurrent.futures import ThreadPoolExecutor


log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_fmt)


app = Flask(__name__)


def create_update_element_history_fixtures_task(element):
    logger = logging.getLogger(__name__)
    logger.info(f'doing element {element}')

    task = {
        'app_engine_http_request': {
            'http_method': 'POST',
            'relative_uri': f'/update_element_history_fixtures/{element}'
        }
    }

    response = utils.create_cloud_task(
        task,
        'update-element-history-fixtures')

    return response


def create_update_entry_picks_chips_task(entry):
    logger = logging.getLogger(__name__)
    logger.info(f'doing entry {entry}')

    task = {
        'app_engine_http_request': {
            'http_method': 'POST',
            'relative_uri': f'/update_entry_picks_chips/{entry}'
        }
    }

    response = utils.create_cloud_task(
        task,
        'update-entry-picks-chips')

    return response


def update_element_history_fixtures_worker(element):
    logger = logging.getLogger(__name__)

    logger.info('getting element gameweek history and fixtures')
    element_history_df, element_fixtures_df = element_data.get_element_history_fixture_dfs(element)

    logger.info('deleting element gameweek history')
    utils.run_query(
        f'DELETE FROM `footbot-001.fpl.element_gameweeks_1920` WHERE element = {element}'
    )
    logger.info('writing element gameweek history')
    utils.write_to_table('fpl',
                         'element_gameweeks_1920',
                         element_history_df)
    logger.info('done writing element gameweek history')

    logger.info('deleting element fixtures')
    utils.run_query(
        f'DELETE FROM `footbot-001.fpl.element_future_fixtures_1920` WHERE element = {element}'
    )
    logger.info('writing element fixtures')
    utils.write_to_table('fpl',
                         'element_future_fixtures_1920',
                         element_fixtures_df)
    logger.info('done writing element fixtures')


def update_entry_picks_chips_worker(entry):
    logger = logging.getLogger(__name__)

    logger.info('getting entry data')
    picks_df, chips_df = entry_data.get_top_entry_dfs(entry)

    logger.info('deleting entry picks')
    utils.run_query(
        f'DELETE FROM `footbot-001.fpl.top_entries_picks_1920` WHERE entry = {entry}'
    )
    logger.info('writing entry picks')
    utils.write_to_table('fpl',
                         'top_entries_picks_1920',
                         picks_df)
    logger.info('done writing entry picks')

    logger.info('deleting entry chips')
    utils.run_query(
        f'DELETE FROM `footbot-001.fpl.top_entries_chips_1920` WHERE entry = {entry}'
    )
    logger.info('writing entry chips')
    utils.write_to_table('fpl',
                         'top_entries_chips_1920',
                         chips_df,)
    logger.info('done writing entry chips')


@app.route('/')
def home_route():
    return 'Greetings!'


@app.route('/update_element_data')
def update_element_data_route():
    logger = logging.getLogger(__name__)

    logger.info('getting element data')
    element_df = element_data.get_element_df()
    logger.info('writing element data')
    utils.write_to_table('fpl',
                         'element_data_1920',
                         element_df)
    logger.info('done writing element data')

    return 'Updated element data, baby'


@app.route('/update_element_history_fixtures')
def update_element_history_fixtures_route():
    logger = logging.getLogger(__name__)

    logger.info('purging queue')
    utils.purge_cloud_queue('update-element-history-fixtures')

    elements = element_data.get_elements()

    with ThreadPoolExecutor(max_workers=50) as executor:
        executor.map(create_update_element_history_fixtures_task, elements)

    return 'elements queued'


@app.route('/update_element_history_fixtures/<element>', methods=['POST'])
def update_element_history_fixtures_element_route(element):
    logger = logging.getLogger(__name__)
    try:
        update_element_history_fixtures_worker(element)
        return 'lovely stuff'
    except Exception as e:
        logger.error(f'Unable to update element {element} with exception {e}')
        return 'bad news!'


@app.route('/update_entry_picks_chips')
def update_entry_picks_chips_route():
    logger = logging.getLogger(__name__)

    logger.info('purging queue')
    utils.purge_cloud_queue('update-entry-picks-chips')

    entries = entry_data.get_top_entries()

    with ThreadPoolExecutor(max_workers=50) as executor:
        executor.map(create_update_entry_picks_chips_task, entries)

    return 'entries queued'


@app.route('/update_entry_picks_chips/<entry>', methods=['POST'])
def update_entry_picks_chips_route(entry):
    logger = logging.getLogger(__name__)
    try:
        update_entry_picks_chips_worker(entry)
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
