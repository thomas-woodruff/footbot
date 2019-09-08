import logging
import schedule
import time
from footbot.data import element_data, utils


def element_data_job():
    element_df = element_data.get_element_df()
    utils.write_to_table('fpl',
                         'element_data',
                         element_df)

    element_history_df, element_fixtures_df = element_data.get_element_summary_dfs()
    utils.write_to_table('fpl',
                         'element_gameweeks',
                         element_history_df,
                         write_disposition='WRITE_TRUNCATE')
    utils.write_to_table('fpl',
                         'element_future_fixtures',
                         element_fixtures_df,
                         write_disposition='WRITE_TRUNCATE')


def main():
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)
    logger = logging.getLogger(__name__)

    # schedule.every().day.at('09:30').do(element_data_job)
    schedule.every(60).seconds.do(element_data_job)

    logger.info('starting schedule')
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    main()