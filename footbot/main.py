import logging
from footbot.data import utils, element_data, entry_data
from footbot.optimiser import team_selector
from flask import Flask, request


log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_fmt)


app = Flask(__name__)


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

    logger.info('getting element gameweek history and fixtures')
    element_history_df, element_fixtures_df = element_data.get_element_summary_dfs()
    logger.info('writing element gameweek history')
    utils.write_to_table('fpl',
                         'element_gameweeks_1920',
                         element_history_df,
                         write_disposition='WRITE_TRUNCATE'
                         )
    logger.info('done writing element gameweek history')
    logger.info('writing element fixtures')
    utils.write_to_table('fpl',
                         'element_future_fixtures_1920',
                         element_fixtures_df,
                         write_disposition='WRITE_TRUNCATE')
    logger.info('done writing element fixtures')

    return 'Updated element gameweek history and fixtures, baby'


# this takes at least a few minutes to run at the moment
#
# @app.route('/update_entry_picks_chips')
# def update_entry_picks_chips():
#     logger = logging.getLogger(__name__)
#
#     logger.info('getting entry data')
#     picks_df, chips_df = entry_data.get_top_entries_dfs()
#     logger.info('writing entry picks')
#     utils.write_to_table('fpl',
#                          'top_entries_picks_1920',
#                          picks_df,
#                          write_disposition='WRITE_TRUNCATE')
#     logger.info('done writing entry picks')
#     logger.info('writing entry chips')
#     utils.write_to_table('fpl',
#                          'top_entries_chips_1920',
#                          chips_df,
#                          write_disposition='WRITE_TRUNCATE')
#     logger.info('done writing entry chips')
#
#     return 'Updated entry picks and chips, baby'


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
