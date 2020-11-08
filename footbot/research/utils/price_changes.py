import numpy as np


def get_player_value(element_all, element_data_df):
    """
    Get the value of a player.
    For players in the squad, their value is their selling price.
    For players not in the squad, their value is their current price.

    :param element_all: Season-agnostic player identifier
    :param element_data_df: Dataframe including values of players
    :return: Value of player
    """

    try:
        value = element_data_df.loc[
            element_data_df["element_all"] == element_all, "value"
        ].iloc[0]
    except IndexError:
        raise Exception("Player missing from `element_data_df`")

    return value


def update_player_value(element_all, updated_value, element_data_df):
    """
    Update the value of a player.

    :param element_all: Season-agnostic player identifier
    :param updated_value: Updated value of player
    :param element_data_df: Dataframe including values of players
    :return: None - updates `element_data_df` in place
    """

    # check player is not missing from element data dataframe
    get_player_value(element_all, element_data_df)

    element_data_df.loc[
        element_data_df["element_all"] == element_all, "value"
    ] = updated_value


def calculate_selling_price(purchase_price, current_price):
    """
    Calculate the selling price of a player in the squad.

    From the FPL rules:
    The price shown on your transfers page is a player's selling price.
    This selling price may be less than the player's current purchase price as a sell-on fee of 50%
    (rounded up to the nearest £0.1m) will be applied on any profits made on that player.

    https://fantasy.premierleague.com/help/rules

    :param purchase_price: Price of player when purchased
    :param current_price: Current price of player
    :return: Selling price of player
    """
    if current_price <= purchase_price:
        return current_price
    else:
        selling_price_change = np.floor((current_price - purchase_price) / 2)
        return purchase_price + selling_price_change


def update_purchase_prices(squad, purchase_price_dict, element_data_df):
    """
    Update the purchase price dictionary to reflect changes in squad.

    When new players are added to the squad, we add their purchase price to the purchase price
    dictionary.
    When existing players are dropped from the squad, we drop them from purchase the price
    dictionary.

    :param squad: List of season-agnostic identifiers (`element_all`) for players in the squad
    :param purchase_price_dict: Dictionary of purchase prices of players in the squad
    :param element_data_df: Dataframe including values of all players
    :return: None - updates `purchase_price_dict` in place
    """
    # add new players to purchase price dictionary
    for element_all in squad:
        if element_all not in purchase_price_dict.keys():
            current_price = get_player_value(element_all, element_data_df)
            purchase_price_dict[element_all] = current_price

    # removed dropped players from purchase price dictionary
    for element_all in list(purchase_price_dict):
        if element_all not in squad:
            del purchase_price_dict[element_all]


def update_player_values_with_selling_prices(element_data_df, purchase_price_dict):
    """
    Update the players values with corresponding selling prices for players in the squad.

    :param element_data_df: Dataframe including values of players
    :param purchase_price_dict: Dictionary of purchase prices of players in the squad
    :return: None - updates `element_data_df` in place
    """

    for element_all, purchase_price in purchase_price_dict.items():
        current_price = get_player_value(element_all, element_data_df)
        selling_price = calculate_selling_price(purchase_price, current_price)
        update_player_value(element_all, selling_price, element_data_df)


def calculate_team_value(squad, element_data_df):
    """
    Calculate the total value of a squad of players.

    :param squad: List of season-agnostic identifiers (`element_all`) for players in the squad
    :param element_data_df: Dataframe including values of all players
    :return: Sum of player values for the squad
    """

    return np.sum([get_player_value(e, element_data_df) for e in squad])
