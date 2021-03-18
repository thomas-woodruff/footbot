import logging

from flask import Flask
from flask import request

from footbot.data import element_data
from footbot.data import utils
from footbot.optimiser import team_selector
from footbot.predictor import train_predict

log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=log_fmt)
logger = logging.getLogger(__name__)


app = Flask(__name__)


def create_update_element_history_fixtures_task(element, client):
    logger.info(f"queueing element {element}")

    task = {
        "app_engine_http_request": {
            "http_method": "POST",
            "relative_uri": f"/update_element_history_fixtures/{element}",
        }
    }

    utils.create_cloud_task(task, "update-element-history-fixtures", client, delay=120)


def update_element_history_fixtures_worker(element, delete=False):
    logger.info(f"setting up client for element {element}")
    client = utils.set_up_bigquery()

    logger.info(f"getting element {element} gameweek history and fixtures")
    (
        element_history_df,
        element_fixtures_df,
    ) = element_data.get_element_history_fixture_dfs(element)

    if delete:
        logger.info(f"deleting element {element} gameweek history")
        utils.run_query(
            f"DELETE FROM `footbot-001.fpl.element_gameweeks_2021` WHERE element = {element}",
            client,
        )

    logger.info(f"writing element {element} gameweek history")
    utils.write_to_table("fpl", "element_gameweeks_2021", element_history_df, client)
    logger.info(f"done writing element {element} gameweek history")

    if delete:
        logger.info(f"deleting element {element} fixtures")
        utils.run_query(
            f"DELETE FROM `footbot-001.fpl.element_future_fixtures_2021` WHERE element = {element}",
            client,
        )

    logger.info(f"writing element {element} fixtures")
    utils.write_to_table(
        "fpl", "element_future_fixtures_2021", element_fixtures_df, client
    )
    logger.info(f"done writing element {element} fixtures")


@app.route("/")
def home_route():
    return "Greetings!"


@app.route("/update_element_data")
def update_element_data_route():
    logger.info("getting element data")
    bootstrap_data = element_data.get_bootstrap()
    element_df = element_data.get_element_df(bootstrap_data)

    client = utils.set_up_bigquery()

    logger.info("writing element data")
    utils.write_to_table("fpl", "element_data_2021", element_df, client)
    logger.info("done writing element data")

    return "Updated element data, baby"


@app.route("/update_element_history_fixtures")
def update_element_history_fixtures_route():
    logger.info("setting up client")
    tasks_client = utils.set_up_tasks()

    logger.info("purging queue")
    utils.purge_cloud_queue("update-element-history-fixtures", tasks_client)

    bootstrap_data = element_data.get_bootstrap()
    elements = element_data.get_elements(bootstrap_data)

    logger.info("setting up big query client")
    big_query_client = utils.set_up_bigquery()

    logger.info("deleting element gameweek history")
    utils.run_query(
        "DELETE FROM `footbot-001.fpl.element_gameweeks_2021` WHERE true",
        big_query_client,
    )
    logger.info("deleting element fixtures")
    utils.run_query(
        "DELETE FROM `footbot-001.fpl.element_future_fixtures_2021` WHERE true",
        big_query_client,
    )

    logger.info("queueing elements")

    for element in elements:
        create_update_element_history_fixtures_task(element, tasks_client)

    logger.info("elements queued")

    return "elements queued"


@app.route("/update_element_history_fixtures/<element>", methods=["POST"])
def update_element_history_fixtures_element_route_post(element):
    try:
        update_element_history_fixtures_worker(element)
        return "lovely stuff"
    except Exception as e:
        logger.error(f"Unable to update element {element} with exception {e}")
        return "bad news!"


@app.route("/update_element_history_fixtures/<element>", methods=["PUT"])
def update_element_history_fixtures_element_route_put(element):
    try:
        update_element_history_fixtures_worker(element, delete=True)
        return "lovely stuff"
    except Exception as e:
        logger.error(f"Unable to update element {element} with exception {e}")
        return "bad news!"


@app.route("/update_predictions")
def update_predictions_route():
    client = utils.set_up_bigquery()

    predict_df = train_predict.get_predicted_points_df(
        "./footbot/predictor/sql/train.sql",
        "./footbot/predictor/sql/predict.sql",
        client,
    )

    logger.info("writing predictions")
    utils.write_to_table(
        "fpl",
        "element_gameweeks_predictions_2021_v01",
        predict_df,
        client,
        write_disposition="WRITE_TRUNCATE",
    )
    logger.info("done writing predictions")

    return "predictions updated"


@app.route("/optimise_team/<entry>", methods=["GET", "POST"])
def optimise_team_route(entry, optimise_entry=team_selector.optimise_entry):

    if request.data and request.content_type != 'application/json':
        return "Request content-type must be application/json", 400

    login = password = None
    try:
        data = request.json
        login = data["login"]
        password = data["password"]
    except TypeError:
        pass
    except KeyError:
        return "Data must contain 'login' and 'password'", 400

    current_event = utils.get_current_event()

    total_budget = int(request.args.get("total_budget", 1000))
    first_team_factor = float(request.args.get("first_team_factor", 0.9))
    bench_factor = float(request.args.get("bench_factor", 0.1))
    captain_factor = float(request.args.get("captain_factor", 0.9))
    vice_factor = float(request.args.get("vice_factor", 0.1))
    transfer_penalty = float(request.args.get("transfer_penalty", 4))
    transfer_limit = int(request.args.get("transfer_limit", 15))
    start_event = int(request.args.get("start_event", current_event + 1))
    end_event = int(request.args.get("end_event", current_event + 1))

    try:
        return optimise_entry(
            entry,
            total_budget=total_budget,
            first_team_factor=first_team_factor,
            bench_factor=bench_factor,
            captain_factor=captain_factor,
            vice_factor=vice_factor,
            transfer_penalty=transfer_penalty,
            transfer_limit=transfer_limit,
            start_event=start_event,
            end_event=end_event,
            login=login,
            password=password,
        )
    except Exception as e:
        logger.error(e)
        return "Uh oh!"


if __name__ == "__main__":
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host="0.0.0.0", port=8022, debug=True)
