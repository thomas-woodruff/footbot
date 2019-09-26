import logging
import schedule
import time
import multiprocessing as mp
from footbot.data import element_data, entry_data, utils
from footbot.api import server

# log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# logging.basicConfig(level=logging.INFO, format=log_fmt)
#
#
# def element_data_job():
#     logger = logging.getLogger(__name__)
#
#     logger.info('getting element data')
#     element_df = element_data.get_element_df()
#     logger.info('writing element data')
#     utils.write_to_table('fpl',
#                          'element_data_1920',
#                          element_df)
#
#     logger.info('getting element gameweeks and fixtures')
#     element_history_df, element_fixtures_df = element_data.get_element_summary_dfs()
#     logger.info('writing element gameweeks')
#     utils.write_to_table('fpl',
#                          'element_gameweeks_1920',
#                          element_history_df,
#                          write_disposition='WRITE_TRUNCATE')
#     logger.info('writing element fixtures')
#     utils.write_to_table('fpl',
#                          'element_future_fixtures_1920',
#                          element_fixtures_df,
#                          write_disposition='WRITE_TRUNCATE')
#
#
# def entry_data_job():
#     logger = logging.getLogger(__name__)
#
#     logger.info('getting entry data')
#     picks_df, chips_df = entry_data.get_top_entries_dfs()
#     logger.info('writing entry picks')
#     utils.write_to_table('fpl',
#                          'top_entries_picks_1920',
#                          picks_df,
#                          write_disposition='WRITE_TRUNCATE')
#     logger.info('writing entry chips')
#     utils.write_to_table('fpl',
#                          'top_entries_chips_1920',
#                          chips_df,
#                          write_disposition='WRITE_TRUNCATE')
#
#
# def scheduled_processes():
#     schedule.every().day.at('09:30').do(element_data_job)
#     schedule.every().day.at('09:35').do(entry_data_job)
#
#     while True:
#         schedule.run_pending()
#         time.sleep(1)
#
#
# def main():
#     logger = logging.getLogger(__name__)
#
#     p = mp.Process(target=scheduled_processes)
#
#     logger.info('starting scheduler')
#     p.start()
#
#     logger.info('starting api')
#     server.run()
#
#
# if __name__ == '__main__':
#     main()

from sanic import Sanic
from sanic.response import json, text
import time

app = Sanic(__name__)


@app.route('/')
async def test(_):
    return text('Greetings!')


@app.get('/status')
async def status(_):
    return json({'OK': time.time(), 'status': 200})


if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)