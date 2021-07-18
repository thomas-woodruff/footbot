import logging

from footbot.data.utils import get_authenticated_session

logger = logging.getLogger(__name__)


def construct_transfers(elements_in, elements_out):
    transfers = []
    for element_in, element_out in zip(elements_in, elements_out):
        transfer = {
            "element_in": element_in["element"],
            "element_out": element_out["element"],
            "purchase_price": element_in["value"],
            "selling_price": element_out["value"],
        }
        transfers.append(transfer)

    return transfers


def make_transfers(current_event, entry, elements_in, elements_out, login, password):
    # todo: check transfers are valid
    transfers = construct_transfers(elements_in, elements_out)
    payload = {
        "entry": entry,
        "event": current_event + 1,
        "transfers": transfers,
        "chip": None,
    }

    session = get_authenticated_session(login, password)

    resp = session.post(
        "https://fantasy.premierleague.com/api/transfers/", json=payload
    )

    return resp
