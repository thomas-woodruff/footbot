import logging
import os
from pprint import pprint
from typing import Optional

import click
from requests.exceptions import HTTPError

from .data.utils import get_authenticated_session
from .main import app
from .optimiser.team_selector import optimise_entry

root = logging.getLogger()
logger = logging.getLogger(__name__)


@click.group()
@click.option("--debug/--no-debug", default=False)
def cli(debug):
    root.setLevel(logging.DEBUG if debug else logging.INFO)


@cli.command()
@click.option("--host", default="0.0.0.0")
@click.option("--port", default=8022)
def serve(host: int, port: int):
    app.run(host=host, port=port, debug=True)


@cli.command()
@click.argument("entry", type=int, nargs=1)
@click.argument("start_event", type=int, nargs=1)
@click.option("--end-event", type=int, default=None)
@click.option("--total-budget", type=int, default=1000)
@click.option("--bench-factor", type=float, default=0.1)
@click.option("--transfer-penalty", type=float, default=0)
@click.option("--transfer-limit", type=int, default=1)
def optimise(
    entry: int,
    start_event: int,
    total_budget: int,
    bench_factor: float,
    transfer_penalty: float,
    transfer_limit: int,
    end_event: Optional[int] = None,
):
    authenticated_session = None
    login = os.environ.get("FPL_LOGIN")
    password = os.environ.get("FPL_PASSWORD")
    if login and password:
        try:
            authenticated_session = get_authenticated_session(login, password, entry)
        except HTTPError:
            logger.info("Login credentials not recognised")
    end_event = start_event + 3 if end_event is None else end_event
    team_data = optimise_entry(
        entry,
        total_budget=total_budget,
        bench_factor=bench_factor,
        transfer_penalty=transfer_penalty,
        transfer_limit=transfer_limit,
        start_event=start_event,
        end_event=end_event,
        authenticated_session=authenticated_session,
    )

    click.echo(pprint(team_data))
