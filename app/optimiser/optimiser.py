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
	    cp.Minimize(player_costs@bench_x),
	    [
	        np.concatenate((player_position_weights,player_team_weights), axis=0)@bench_x <= np.array(bench_position_capacity + bench_team_capacity),
	        np.ones(len(players))@bench_x == bench_num
	    ]
	)

	min_cost_bench = bench_cost_prob.solve()





	# min_cost_keeper = np.min([i['value'] for i in players if i['element_type'] == 1])
	# min_cost_defender = np.min([i['value'] for i in players if i['element_type'] == 2])
	# min_cost_midfielder = np.min([i['value'] for i in players if i['element_type'] == 3])
	# min_cost_striker = np.min([i['value'] for i in players if i['element_type'] == 4])
	# min_cost_bench = \
	# bench_position_capacity@np.array([min_cost_keeper, min_cost_defender, min_cost_midfielder, min_cost_striker])

	
	bench_cost_capacity = [min_cost_bench]

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
	player_cost_capacity = [total_budget - min_cost_bench]
	player_team_capacity = list(bench_team_capacity - player_team_weights@bench_selection) #[3]*20

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

