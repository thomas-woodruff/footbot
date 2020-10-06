import logging
from pathlib import Path
from pprint import pprint
from typing import Optional

import click

from .data.utils import run_query
from .data.utils import set_up_bigquery
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
@click.argument("team_id", type=int, nargs=1)
@click.argument("start_event", type=int, nargs=1)
@click.option("--end-event", type=int, default=None)
@click.option("--total-budget", type=int, default=1000)
@click.option("--bench-factor", type=float, default=0.1)
@click.option("--transfer-penalty", type=float, default=0)
@click.option("--transfer-limit", type=int, default=1)
@click.option("--private", type=bool, default=True)
def optimise(
    team_id: int,
    start_event: int,
    total_budget: int,
    bench_factor: float,
    transfer_penalty: float,
    transfer_limit: int,
    end_event: Optional[int] = None,
    private: bool = True,
):
    end_event = start_event + 3 if end_event is None else end_event
    team_data = optimise_entry(
        team_id,
        total_budget=total_budget,
        bench_factor=bench_factor,
        transfer_penalty=transfer_penalty,
        transfer_limit=transfer_limit,
        start_event=start_event,
        end_event=end_event,
        private=private,
    )

    click.echo(pprint(team_data))


@cli.command()
@click.argument("table_name", type=str, nargs=1)
@click.option("--output-directory", type=Path, default=None)
@click.option("--limit", type=int, default=None)
def dump(table_name: str, output_directory: Path, limit: int):
    logger.debug(f"Dumping {table_name} to {output_directory}")
    if output_directory is None:
        output_directory = Path(__file__).parent.parent / "dumps"
    output_directory.mkdir(parents=True, exist_ok=True)
    client = set_up_bigquery()
    query = f"""
        SELECT
            *
        FROM
            `footbot-001.fpl.{table_name}`
    """ + (
        f" LIMIT {limit}" if limit else ""
    )
    df = run_query(query, client)
    df.to_pickle(output_directory / f"{table_name}.pkl")
