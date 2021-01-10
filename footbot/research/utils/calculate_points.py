def calculate_points(
    first_team_dicts,
    bench_dicts,
    transfers_made,
    free_transfers_available,
    triple_captain=False,
    bench_boost=False,
):
    """
    Calculate the total gameweek points for a squad, including chips and transfers.

    More information on chips can be found here:
    https://fantasy.premierleague.com/help/rules

    :param first_team_dicts: Array of dicts representing first team
    :param bench_dicts: Array of dicts representing bench
    :param transfers_made: Number of transfers made
    :param free_transfers_available: Number of free transfers available
    :param triple_captain: Boolean indicating use of triple captain chip
    :param bench_boost: Boolean indicating use of bench boost chip
    :return: Total points
    """

    first_team_points = sum(
        [i["total_points"] for i in first_team_dicts if not i["is_captain"]]
    )

    if triple_captain:
        captain_multiplier = 3
    else:
        captain_multiplier = 2

    captain_points = sum(
        [
            i["total_points"] * captain_multiplier
            for i in first_team_dicts
            if i["is_captain"]
        ]
    )

    if bench_boost:
        bench_points = sum([i["total_points"] for i in bench_dicts])
    else:
        bench_points = 0

    transfer_points = min(-4 * (transfers_made - free_transfers_available), 0)

    return first_team_points + captain_points + bench_points + transfer_points
