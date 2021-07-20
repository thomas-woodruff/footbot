import logging

from footbot.optimiser.team_selector import optimise_entry
from footbot.optimiser.settings import FIRST_TEAM_FACTOR
from footbot.optimiser.settings import BENCH_FACTOR
from footbot.optimiser.settings import CAPTAIN_FACTOR
from footbot.optimiser.settings import VICE_FACTOR

from footbot.data.utils import get_current_event

logger = logging.getLogger(__name__)


def sort_players_into_position(players):
    return sorted(players, key=lambda x: (x["element_type"], x["element"]))


def construct_picks_list(first_team, bench, captain, vice):

    squad = sort_players_into_position(first_team) + sort_players_into_position(bench)

    picks = []
    for index, player in enumerate(squad):
        pick = {
            "element": player['element'],
            "position": index + 1,
            "is_captain": player['element'] == captain[0]['element'],
            "is_vice_captain": player['element'] == vice[0]['element']
        }
        picks.append(pick)

    return picks


def make_team_selection(entry, first_team, bench, captain, vice, authenticated_session):

    picks = construct_picks_list(first_team, bench, captain, vice)
    payload = {
        "picks": picks,
        "chip": None,
    }

    resp = authenticated_session.post(
        f"https://fantasy.premierleague.com/api/my-team/{entry}/", json=payload
    )

    return resp


def make_optimised_team_selection(
        entry,
        authenticated_session,
        first_team_factor=FIRST_TEAM_FACTOR,
        bench_factor=BENCH_FACTOR,
        captain_factor=CAPTAIN_FACTOR,
        vice_factor=VICE_FACTOR,

):

    current_event = get_current_event()
    start_event = current_event + 1
    end_event = start_event

    optimiser_results = optimise_entry(
        entry,
        first_team_factor=first_team_factor,
        bench_factor=bench_factor,
        captain_factor=captain_factor,
        vice_factor=vice_factor,
        transfer_penalty=0,
        transfer_limit=0,
        start_event=start_event,
        end_event=end_event,
        authenticated_session=authenticated_session,
        readable=False,
    )

    first_team = optimiser_results['first_team']
    bench = optimiser_results['bench']
    captain = optimiser_results['captain']
    vice = optimiser_results['vice']
    resp = make_team_selection(entry, first_team, bench, captain, vice, authenticated_session)

    return resp, optimiser_results
