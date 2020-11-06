from collections import Counter


def check_valid_formation(first_team):
    '''
    Check candidate first team has a valid formation.

    https://fantasy.premierleague.com/help
    "Your team must have 1 goalkeeper, at least 3 defenders and at least 1 forward"

    :param first_team: Array of dicts representing first team
    :return: Boolean indicating validity
    '''

    c = Counter(i['element_type'] for i in first_team)

    keepers = c[1] == 1
    defenders = c[2] >= 3
    forwards = c[4] >= 1

    return all([keepers, defenders, forwards])


def make_subs(first_team, bench):
    '''
    Substitute missing players in the first team for players on the bench, ensuring valid formation.

    :param first_team: Array of dicts representing first team
    :param bench: Array of dicts representing bench
    :return: Tuple of updated first_team and bench
    '''

    squad = first_team + bench
    missing_players = [i for i in first_team if i['minutes'] == 0]

    for b in bench:
        for m in missing_players:
            candidate_first_team = [i for i in first_team if i['element'] != m['element']] + [b]

            if check_valid_formation(candidate_first_team):
                first_team = candidate_first_team
                missing_players.remove(m)
                break

    bench = [i for i in squad if i not in first_team]

    return first_team, bench


def get_captain(captain, vice):
    return "bar"

