import requests
import logging
import json

logger = logging.getLogger(__name__)


def get_authenticated_session(login, password):
    session = requests.session()

    payload = {
        "redirect_uri": "https://fantasy.premierleague.com/a/login",
        "app": "plfpl-web",
        "login": login,
        "password": password,
    }

    logger.info("authenticating for entry")
    resp = session.post("https://users.premierleague.com/accounts/login/", data=payload)
    resp.raise_for_status()

    return session


def construct_transfers(elements_in, elements_out):
    transfers = []
    for element_in, element_out in zip(elements_in, elements_out):
        transfer = {
            "element_in": element_in["element"],
            "element_out": element_out["element"],
            "purchase_price": element_in["now_cost"],
            "selling_price": element_out["now_cost"]
        }
        transfers.append(transfer)

    return transfers


def make_transfers(
        current_event,
        entry,
        elements_in,
        elements_out,
        login,
        password
):
    # todo: check transfers are valid
    transfers = construct_transfers(elements_in, elements_out)
    payload = {
            "entry": entry,
            "event": current_event + 1,
            "transfers": transfers,
            "chip": None
    }
    print(payload)

    session = get_authenticated_session(login, password)
    current_team = session.get(
        f"https://fantasy.premierleague.com/api/my-team/{entry}"
    ).json()
    print(current_team)

    resp = session.post(
        'https://fantasy.premierleague.com/api/transfers/',
        json=payload
    )

    return resp