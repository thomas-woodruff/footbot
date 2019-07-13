import pandas as pd
import knapsack
import cvxpy as cp
import numpy as np

def construct_optimal_team_from_scratch(
	players,
	total_budget=1000,
	formation=[1, 4, 5, 1],
	optimise_key='predicted_total_points',
	black_list_players=[]
	):

	player_elements = np.array([i['element'] for i in players])
	player_points = np.array([i[optimise_key] for i in players])/38
	player_costs = np.array([[i['value'] for i in players]])
	player_position = np.array([i['element_type'] for i in players])
	player_team = np.array([i['team'] for i in players])

	player_position_weights = np.zeros((4, len(players)))
	for i in range(0, 4):
	    for j in range(0, len(players)):
	        if player_position[j] == i+1:
	            player_position_weights[i, j] = 1
	        else:
	            player_position_weights[i, j] = 0

	player_team_weights = np.zeros((20, len(players)))
	for i in range(0, 20):
	    for j in range(0, len(players)):
	        if player_team[j] == i+1:
	            player_team_weights[i, j] = 1
	        else:
	            player_team_weights[i, j] = 0

	player_weights = np.concatenate((
	    player_costs,
	    player_position_weights,
	    player_team_weights
	), axis=0)
	
	
	bench_num = 4
	player_position_capacity = formation
	bench_position_capacity = list(np.array([2, 5, 5, 3]) - np.array(player_position_capacity))
	bench_team_capacity = [3]*20

	
	bench_cost_x = cp.Variable(len(players), boolean=True)

	bench_cost_prob = cp.Problem(
	    cp.Minimize(player_costs@bench_cost_x),
	    [
	        np.concatenate((player_position_weights,player_team_weights), axis=0)@bench_cost_x <= np.array(bench_position_capacity + bench_team_capacity),
	        np.ones(len(players))@bench_cost_x == bench_num
	    ]
	)

	
	bench_cost_capacity = [bench_cost_prob.solve()]

	bench_capacity = np.array(
	    bench_cost_capacity
	    + bench_position_capacity
	    + bench_team_capacity
	)

	bench_x = cp.Variable(len(players), boolean=True)

	bench_prob = cp.Problem(
	    cp.Maximize(player_points@bench_x),
	    [
	        player_weights@bench_x <= bench_capacity,
	        np.ones(len(players))@bench_x == bench_num
	    ]
	)

	bench_prob.solve()
	bench_selection = [int(round(j)) for j in bench_x.value]
	bench_selection_indices = [i for i, j in enumerate(bench_selection) if j == 1]
	bench_selection_elements = player_elements[bench_selection_indices]


	player_num = 11
	player_cost_capacity = [total_budget - bench_cost_capacity[0]]
	player_team_capacity = list(bench_team_capacity - player_team_weights@bench_selection)

	player_capacity = np.array(
	    player_cost_capacity
	    + player_position_capacity
	    + player_team_capacity
	)

	player_x = cp.Variable(len(players), boolean=True)

	player_prob = cp.Problem(
	    cp.Maximize(player_points@player_x),
	    [
	        player_weights@player_x <= player_capacity,
	        np.ones(len(players))@player_x == player_num,
	        np.array(bench_selection)@player_x <= 0.01
	    ]
	)

	player_prob.solve()
	player_selection = [int(round(j)) for j in player_x.value]
	player_selection_indices = [i for i, j in enumerate(player_selection) if j == 1]
	player_selection_elements = player_elements[player_selection_indices]

	return player_selection_elements, bench_selection_elements


def calculate_team_total_points(df, first_team_elements, bench_elements):
    df = df.copy()
    df = df[df['element'].isin(list(first_team_elements) + list(bench_elements))]
    df['is_first_team'] = 0
    df.loc[df['element'].isin(list(first_team_elements)),'is_first_team'] = 1

    df['is_first_team'] = df['element'].apply(lambda x: 1 if x in first_team_elements else 0)

    df_group = df.groupby('element')[['predicted_total_points', 'total_points', 'minutes']].sum()

    df = df[['safe_web_name', 'element', 'value', 'element_type', 'is_first_team']].drop_duplicates()

    df = df.join(df_group, on='element')

    df.sort_values('predicted_total_points', ascending=False, inplace=True)

    captain_selection = df.iloc[0]['element']
    vice_selection = df.iloc[1]['element']

    is_captain_missing = len(df[(df['element'] == captain_selection) & (df['minutes'] == 0)])

    if is_captain_missing:
        df['is_captain'] = df['element'].apply(lambda x: 1 if x == vice_selection else 0)
    else:
        df['is_captain'] = df['element'].apply(lambda x: 1 if x == captain_selection else 0)

    missing_players = list(df[(df['minutes'] == 0) & (df['is_first_team'] == 1)]['element'])
    print(missing_players)
    num_missing_players = len(missing_players)

    if num_missing_players > 0:

        num_keepers = 1
        min_defenders = 3
        min_midfielders = 2
        min_strikers = 1

        df[df['minutes'] == 0]

        for i in range(0, min(3, num_missing_players)):
            substitute = df[df['is_first_team'] == 0].iloc[i]['element']

            for missing_player in missing_players:
                print(missing_player)
                sub_loop_df = df.copy()

                sub_loop_df.loc[sub_loop_df['element'] == substitute,'is_first_team'] = 1
                sub_loop_df.loc[sub_loop_df['element'] == missing_player,'is_first_team'] = 0

                num_team_keepers = len(
                    sub_loop_df[(sub_loop_df['is_first_team'] == 1) & (sub_loop_df['element_type'] == 1)])
                num_team_defenders = len(
                    sub_loop_df[(sub_loop_df['is_first_team'] == 1) & (sub_loop_df['element_type'] == 2)])
                num_team_midfielders = len(
                    sub_loop_df[(sub_loop_df['is_first_team'] == 1) & (sub_loop_df['element_type'] == 3)])
                num_team_strikers = len(
                    sub_loop_df[(sub_loop_df['is_first_team'] == 1) & (sub_loop_df['element_type'] == 4)])

                if (
                    (num_team_keepers == num_keepers)
                    & (num_team_defenders >= min_defenders)
                    & (num_team_midfielders >= min_midfielders)
                    & (num_team_strikers >= min_strikers)
                ):
                    df = sub_loop_df.copy()
                    missing_players = df[(df['minutes'] == 0) & (df['is_first_team'] == 1)]
                    num_missing_players = len(missing_players)
                    break


    team_total_points = \
    sum(df[df['is_first_team'] == 1]['total_points'] * (df[df['is_first_team'] == 1]['is_captain'] + 1))

    team_predicted_total_points = \
    sum(df[df['is_first_team'] == 1]['predicted_total_points'] * (df[df['is_first_team'] == 1]['is_captain'] + 1))

    return team_total_points, team_predicted_total_points, df