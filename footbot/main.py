import logging
import schedule
import time
from footbot.data import element_data


def element_data_job():
    element_data.get_element_df()
    print('ahoy!')


def main():
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)
    logger = logging.getLogger(__name__)

    schedule.every().minute.at(":17").do(element_data_job)

    logger.info("starting schedule")
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()