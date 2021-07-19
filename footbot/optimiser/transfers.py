import logging

from footbot.optimiser.team_selector import optimise_entry
from footbot.optimiser.settings import FIRST_TEAM_FACTOR
from footbot.optimiser.settings import BENCH_FACTOR
from footbot.optimiser.settings import CAPTAIN_FACTOR
from footbot.optimiser.settings import VICE_FACTOR
from footbot.optimiser.settings import TRANSFER_PENALTY
from footbot.optimiser.settings import TRANSFER_LIMIT
from footbot.optimiser.settings import EVENTS_TO_LOOK_AHEAD

from footbot.data.utils import get_current_event
from footbot.data.utils import get_authenticated_session

logger = logging.getLogger(__name__)


def construct_transfers_dict(transfers_in, transfers_out):
    transfers = []
    for transfer_in, transfer_out in zip(transfers_in, transfers_out):
        transfer = {
            "element_in": transfer_in["element"],
            "element_out": transfer_out["element"],
            "purchase_price": transfer_in["value"],
            "selling_price": transfer_out["value"],
        }
        transfers.append(transfer)

    return transfers


def make_transfers(current_event, entry, transfers_in, transfers_out, authenticated_session):

    # todo: check transfers are valid

    transfers = construct_transfers_dict(transfers_in, transfers_out)
    payload = {
        "entry": entry,
        "event": current_event + 1,
        "transfers": transfers,
        "chip": None,
    }

    resp = authenticated_session.post(
        "https://fantasy.premierleague.com/api/transfers/", json=payload
    )

    return resp


def make_optimised_transfers(
        entry,
        authenticated_session
):

    current_event = get_current_event()
    start_event = current_event + 1
    end_event = start_event + EVENTS_TO_LOOK_AHEAD

    optimiser_results = optimise_entry(
        entry,
        first_team_factor=FIRST_TEAM_FACTOR,
        bench_factor=BENCH_FACTOR,
        captain_factor=CAPTAIN_FACTOR,
        vice_factor=VICE_FACTOR,
        transfer_penalty=TRANSFER_PENALTY,
        transfer_limit=TRANSFER_LIMIT,
        start_event=start_event,
        end_event=end_event,
        authenticated_session=authenticated_session,
        readable=False,
    )

    transfers_in = optimiser_results['transfers_in']
    transfers_out = optimiser_results['transfers_out']
    resp = make_transfers(
        current_event, entry, transfers_in, transfers_out, authenticated_session)

    return resp
