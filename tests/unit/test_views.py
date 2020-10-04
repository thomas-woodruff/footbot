from unittest.mock import Mock

import pytest

from footbot.main import app
from footbot.main import optimise_team_route


@pytest.fixture
def flask_app():
    yield app


def test_optimise_team_route_public(flask_app):
    optimise_entry = Mock()
    with flask_app.test_request_context(
        "?total_budget=2345"
        "&bench_factor=0.5"
        "&transfer_penalty=5.0"
        "&transfer_limit=20"
        "&start_event=10"
        "&end_event=20"
    ):
        assert (
            optimise_team_route(1234, optimise_entry=optimise_entry)
            == optimise_entry.return_value
        )
        optimise_entry.assert_called_once_with(
            1234,
            total_budget=2345,
            bench_factor=0.5,
            transfer_penalty=5.0,
            transfer_limit=20,
            start_event=10,
            end_event=20,
            private=False,
        )
