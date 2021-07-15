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
        data=payload
    )

    return resp


## GENERAL
# Request URL: https://fantasy.premierleague.com/api/transfers/
# Request Method: POST
# Status Code: 200
# Remote Address: 151.101.62.133:443
# Referrer Policy: strict-origin-when-cross-origin

## RESPONSE HEADERS
# accept-ranges: bytes
# allow: POST, OPTIONS
# cache-control: max-age=0, no-cache, no-store, must-revalidate, private
# content-length: 0
# date: Thu, 15 Jul 2021 11:57:42 GMT
# referrer-policy: same-origin
# server: nginx/1.19.10
# vary: Cookie
# via: 1.1 google, 1.1 varnish
# x-cache: MISS
# x-cache-hits: 0
# x-content-type-options: nosniff
# x-frame-options: DENY
# x-served-by: cache-lhr7355-LHR
# x-timer: S1626350262.073598,VS0,VE72

## REQUEST HEADERS
# :authority: fantasy.premierleague.com
# :method: POST
# :path: /api/transfers/
# :scheme: https
# accept: */*
# accept-encoding: gzip, deflate, br
# accept-language: en-US,en;q=0.9
# content-length: 128
# content-type: application/json
# cookie: pl_profile="eyJzIjogIld6SXNOREE1TkRjM056bGQ6MW0zd3dOOkREMUsybWJOdXBhMGRBcEVIVTFmc3RVWWRYbVYwelRSWkdtZ1ZjcEhOSzAiLCAidSI6IHsiaWQiOiA0MDk0Nzc3OSwgImZuIjogIkxhdXJhIiwgImxuIjogIldvb2RydWZmIiwgImZjIjogNDN9fQ=="; csrftoken=irKSd2vB1FxOup57Shs6I2OQJVcPwKMLp4HicVAUETr6RfNoZl5DrNHcd9IiSs7A; sessionid=.eJxVy8sKwjAQheF3yVrK5DKZjDv3gkJxHdJciFhKMXYlvrvpTpeH7_xv4cP2qn5r-envSRyFATZExOLwS1OIj7zsvs5lnYddhuv51q2N4-XU539QQ6v9LTEogIAJEwEpCQYB1ZSRLDllGcgyJ4sgNSWlHeniWBPGYhhkBPH5ArMgMNQ:1m3wwO:vwmQtSCnezLjfBm7BzUn7VdizX3VLRSNDBC0i1SUmis; _ga=GA1.3.1298043502.1620577830; _gid=GA1.3.1711853114.1626337870; _ga=GA1.2.1298043502.1620577830; _gid=GA1.2.1711853114.1626337870; _dc_gtm_UA-33785302-1=1
# origin: https://fantasy.premierleague.com
# referer: https://fantasy.premierleague.com/transfers
# sec-ch-ua: " Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"
# sec-ch-ua-mobile: ?0
# sec-fetch-dest: empty
# sec-fetch-mode: cors
# sec-fetch-site: same-origin
# user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36
# x-csrftoken: irKSd2vB1FxOup57Shs6I2OQJVcPwKMLp4HicVAUETr6RfNoZl5DrNHcd9IiSs7A

## REQUEST PAYLOAD
# {"chip":null,"entry":1052042,"event":1,"transfers":[{"element_in":376,"element_out":28,"purchase_price":40,"selling_price":40}]}