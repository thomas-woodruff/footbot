import pandas as pd
import pytest

from footbot.research.utils.price_changes import calculate_selling_price
from footbot.research.utils.price_changes import calculate_team_value
from footbot.research.utils.price_changes import get_player_value
from footbot.research.utils.price_changes import update_player_value
from footbot.research.utils.price_changes import (
    update_player_values_with_selling_prices,
)
from footbot.research.utils.price_changes import update_purchase_prices


def test_get_player_value():
    element_data_df = pd.DataFrame([{"element_all": 1, "value": 45}])

    assert get_player_value(1, element_data_df) == 45

    with pytest.raises(Exception) as e:
        get_player_value(2, element_data_df)
    assert "Player missing from `element_data_df`" in str(e.value)


def test_update_player_value():
    element_data_df = pd.DataFrame([{"element_all": 1, "value": 45}])

    update_player_value(1, 46, element_data_df)
    assert get_player_value(1, element_data_df) == 46

    with pytest.raises(Exception) as e:
        update_player_value(2, 40, element_data_df)
    assert "Player missing from `element_data_df`" in str(e.value)


def test_calculate_selling_price():
    # no price change
    assert calculate_selling_price(40, 40) == 40
    # odd price change
    assert calculate_selling_price(40, 45) == 42
    # even price change
    assert calculate_selling_price(40, 46) == 43
    # price fall
    assert calculate_selling_price(40, 39) == 39


def test_update_purchase_prices():
    purchase_price_dict = {
        1: 40,
        2: 50,
    }
    squad = [1, 3]

    element_data_df = pd.DataFrame(
        [
            {"element_all": 1, "value": 45},
            {"element_all": 2, "value": 50},
            {"element_all": 3, "value": 60},
        ]
    )

    update_purchase_prices(squad, purchase_price_dict, element_data_df)

    # existing player price not updated
    assert purchase_price_dict[1] == 40
    # player added to squad
    assert purchase_price_dict[3] == 60
    # player dropped from squad
    with pytest.raises(KeyError):
        purchase_price_dict[2]


def test_update_player_values_with_selling_prices():
    purchase_price_dict = {1: 40}
    element_data_df = pd.DataFrame(
        [{"element_all": 1, "value": 45}, {"element_all": 2, "value": 50}]
    )

    update_player_values_with_selling_prices(element_data_df, purchase_price_dict)

    # selling price for player in squad
    assert get_player_value(1, element_data_df) == 42
    # current price for player not in squad
    assert get_player_value(2, element_data_df) == 50


def test_calculate_team_value():
    squad = [1, 2]

    element_data_df = pd.DataFrame(
        [
            {"element_all": 1, "value": 40},
            {"element_all": 2, "value": 50},
            {"element_all": 3, "value": 60},
        ]
    )

    assert calculate_team_value(squad, element_data_df) == 90
