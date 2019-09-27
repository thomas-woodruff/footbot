import logging
from footbot.data import element_data, entry_data, utils
from footbot.optimiser import team_selector
from flask import Flask, request
import multiprocessing as mp
import os


log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_fmt)


def element_data_job():
    logger = logging.getLogger(__name__)

    logger.info('getting element data')
    element_df = element_data.get_element_df()
    logger.info('writing element data')
    utils.write_to_table('fpl',
                         'element_data_1920',
                         element_df)

    logger.info('getting element gameweeks and fixtures')
    element_history_df, element_fixtures_df = element_data.get_element_summary_dfs()
    logger.info('writing element gameweeks')
    utils.write_to_table('fpl',
                         'element_gameweeks_1920',
                         element_history_df,
                         write_disposition='WRITE_TRUNCATE')
    logger.info('writing element fixtures')
    utils.write_to_table('fpl',
                         'element_future_fixtures_1920',
                         element_fixtures_df,
                         write_disposition='WRITE_TRUNCATE')


def entry_data_job():
    logger = logging.getLogger(__name__)

    logger.info('getting entry data')
    picks_df, chips_df = entry_data.get_top_entries_dfs()
    logger.info('writing entry picks')
    utils.write_to_table('fpl',
                         'top_entries_picks_1920',
                         picks_df,
                         write_disposition='WRITE_TRUNCATE')
    logger.info('writing entry chips')
    utils.write_to_table('fpl',
                         'top_entries_chips_1920',
                         chips_df,
                         write_disposition='WRITE_TRUNCATE')


app = Flask(__name__)


@app.route('/')
def home_route():
    return 'Greetings!'


@app.route('/update_data')
def update_data_route():
    # element_data_process = mp.Process(target=element_data_job)
    # entry_data_process = mp.Process(target=entry_data_job)
    #
    # element_data_process.start()
    # entry_data_process.start()
    print(os.getcwd())
    print('getting element data')
    element_df = element_data.get_element_df()
    print('writing element data')
    utils.write_to_table('fpl',
                         'element_data_1920',
                         element_df)

    return 'Running hot, baby'


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
