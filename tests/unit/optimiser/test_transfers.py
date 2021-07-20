import pytest

from footbot.optimiser.transfers import construct_transfers_list

@pytest.fixture
def transfers_in():
    transfers_in = [
        {
            "element": 1,
            "key": 4,
            "value": 40,
            "element_type": 1,
            "team": 1,
            "safe_web_name": "alex",
        },
        {
            "element": 2,
            "key": 5,
            "value": 40,
            "element_type": 1,
            "team": 2,
            "safe_web_name": "ben",
        }
    ]
    return transfers_in

@pytest.fixture
def transfers_out():
    transfers_out = [
        {
            "element": 3,
            "key": 4,
            "value": 40,
            "element_type": 1,
            "team": 1,
            "safe_web_name": "alex",
        },
        {
            "element": 4,
            "key": 5,
            "value": 40,
            "element_type": 1,
            "team": 2,
            "safe_web_name": "ben",
        }
    ]
    return transfers_out


def test_construct_transfers_list(transfers_in, transfers_out):
    assert construct_transfers_list(transfers_in, transfers_out) == [
        {
            "element_in": 1,
            "element_out": 3,
            "purchase_price": 40,
            "selling_price": 40,
        },
        {
            "element_in": 2,
            "element_out": 4,
            "purchase_price": 40,
            "selling_price": 40,
        }
    ]

    assert construct_transfers_list([], []) == []