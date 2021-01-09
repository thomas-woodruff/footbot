from collections import Counter


def check_valid_formation(first_team_dicts):
    """
    Check candidate first team has a valid formation.

    https://fantasy.premierleague.com/help
    "Your team must have 1 goalkeeper, at least 3 defenders and at least 1 forward"

    :param first_team_dicts: Array of dicts representing first team
    :return: Boolean indicating validity
    """

    c = Counter(i["element_type"] for i in first_team_dicts)

    keepers = c[1] == 1
    defenders = c[2] >= 3
    forwards = c[4] >= 1

    return all([keepers, defenders, forwards])


def make_subs(first_team_dicts, bench_dicts):
    """
    Substitute missing players in the first team for players on the bench, ensuring valid formation.

    :param first_team_dicts: Array of dicts representing first team
    :param bench_dicts: Array of dicts representing bench
    :return: Tuple of updated first_team_dicts and bench
    """

    squad = first_team_dicts + bench_dicts
    missing_players = [i for i in first_team_dicts if i["minutes"] == 0]

    for b in bench_dicts:
        for m in missing_players:
            candidate_first_team_dicts = [
                i for i in first_team_dicts if i["element"] != m["element"]
            ] + [b]

            if check_valid_formation(candidate_first_team_dicts):
                first_team_dicts = candidate_first_team_dicts
                missing_players.remove(m)
                break

    bench_dicts = [i for i in squad if i not in first_team_dicts]

    return first_team_dicts, bench_dicts


def pick_captain(first_team_dicts):
    """
    Change the captain and vice if necessary.

    If the captain doesn't play, the vice becomes captain.
    If both vice and captain don't play, there is no captain.

    :param first_team_dicts: Array of dicts representing first team
    :return: Array of dicts representing updated first team
    """
    captain_minutes = [i["minutes"] for i in first_team_dicts if i["is_captain"]][0]
    vice_minutes = [i["minutes"] for i in first_team_dicts if i["is_vice"]][0]

    if captain_minutes == 0:
        for player in first_team_dicts:
            if player["is_captain"]:
                player["is_captain"] = False
        for player in first_team_dicts:
            if player["is_vice"]:
                player["is_vice"] = False
                if vice_minutes > 0:
                    player["is_captain"] = True

    return first_team_dicts
