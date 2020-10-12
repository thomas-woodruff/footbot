from unittest.mock import ANY
from unittest.mock import Mock

import pytest

from footbot.main import app
from footbot.main import home_route
from footbot.main import optimise_team_route


def test_home_route():
    assert "Greetings" in home_route()


@pytest.fixture
def flask_app():
    yield app


def test_optimise_team_route_public(flask_app):
    optimise_entry = Mock()
    with flask_app.test_request_context(
        "?total_budget=2345"
        "&first_team_factor=0.5"
        "&bench_factor=0.5"
        "&captain_factor=0.5"
        "&vice_factor=0.5"
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
            first_team_factor=0.5,
            bench_factor=0.5,
            captain_factor=0.5,
            vice_factor=0.5,
            transfer_penalty=5.0,
            transfer_limit=20,
            start_event=10,
            end_event=20,
            login=None,
            password=None,
        )


def test_optimise_team_route_private_bad_data(flask_app):
    optimise_entry = Mock()
    with flask_app.test_request_context(json={"foo": "bar"}):
        resp, code = optimise_team_route(1234, optimise_entry=optimise_entry)
    assert code == 400


def test_optimise_team_route_private(flask_app):
    optimise_entry = Mock()
    with flask_app.test_request_context(
        json={"login": "login", "password": "password"}
    ):
        assert (
            optimise_team_route(1234, optimise_entry=optimise_entry)
            == optimise_entry.return_value
        )
        optimise_entry.assert_called_once_with(
            1234,
            total_budget=ANY,
            first_team_factor=ANY,
            bench_factor=ANY,
            captain_factor=ANY,
            vice_factor=ANY,
            transfer_penalty=ANY,
            transfer_limit=ANY,
            start_event=ANY,
            end_event=ANY,
            login="login",
            password="password",
        )
