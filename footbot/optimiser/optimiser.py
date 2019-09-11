import cvxpy as cp
import numpy as np


def select_team(
		players,
		total_budget=1000,
		optimise_key='predicted_total_points',
		captain_factor=2,
		bench_factor=0.1,
		existing_squad_elements=None,
		transfer_penalty=4,
		transfer_limit=15
):
	'''
	solve team selection from scratch
	players is an array of dicts
	'''

	# munge player data
	player_elements = np.array([i['element'] for i in players])
	player_points = np.array([i[optimise_key] for i in players])
	player_costs = np.array([[i['value'] for i in players]])
	player_position = np.array([i['element_type'] for i in players])
	player_club = np.array([i['team'] for i in players])

	if existing_squad_elements:
		existing_squad = \
			np.array([1 if i in existing_squad_elements else 0 for i in player_elements])

		if sum(existing_squad) != 15:
			raise Exception

	# weight matrix for player positions
	player_position_weights = np.zeros((4, len(players)))
	for i in range(0, 4):
		for j in range(0, len(players)):
			if player_position[j] == i + 1:
				player_position_weights[i, j] = 1
			else:
				player_position_weights[i, j] = 0

	# weight matrix for player clubs
	player_club_weights = np.zeros((20, len(players)))
	for i in range(0, 20):
		for j in range(0, len(players)):
			if player_club[j] == i + 1:
				player_club_weights[i, j] = 1
			else:
				player_club_weights[i, j] = 0

	# overall weight matrix
	player_weights = np.concatenate((
		player_costs,
		player_club_weights
	), axis=0)

	# capacity vector
	squad_cost_capacity = [total_budget]
	squad_club_capacity = [3] * 20
	squad_capacity = np.array(
		squad_cost_capacity
		+ squad_club_capacity
	)

	# variables for objective function
	first_team = cp.Variable(len(players), boolean=True)
	captain = cp.Variable(len(players), boolean=True)
	bench = cp.Variable(len(players), boolean=True)

	# objective function (no existing squad)
	objective = \
		player_points @ first_team + captain_factor * player_points @ captain + bench_factor * player_points @ bench

	# optimisation constraints (no existing squad)
	constraints = [
		# cost and club constraints
		player_weights @ (first_team + bench) <= squad_capacity,
		# position constraints
		player_position_weights @ (first_team + bench) == [2, 5, 5, 3],
		player_position_weights @ first_team >= [1, 3, 3, 1],
		player_position_weights @ first_team <= [1, 5, 5, 3],
		# player number contraints
		np.ones(len(players)) @ first_team == 11,
		np.ones(len(players)) @ captain == 1,
		np.ones(len(players)) @ bench == 4,
		# selected players not on both first team and bench
		first_team + bench <= np.ones(len(players)),
		# first team contains captain
		first_team - captain >= np.zeros(len(players))
	]

	# update objective function and constraints if existing squad
	if existing_squad_elements:
		objective = \
			objective - transfer_penalty * (15 - existing_squad @ (first_team + bench))

		constraints.append(
			15 - existing_squad @ (first_team + bench) <= transfer_limit
		)

	# optimisation problem
	squad_prob = cp.Problem(
		cp.Maximize(objective),
		constraints
	)

	# solve optimisation problem
	squad_prob.solve(
		# solver='GLPK_MI'
	)

	# get first team elements
	first_team_selection = [int(round(j)) for j in first_team.value]
	first_team_selection_indices = [i for i, j in enumerate(first_team_selection) if j == 1]
	first_team_selection_elements = player_elements[first_team_selection_indices]
	# get captain element
	captain_selection = [int(round(j)) for j in captain.value]
	captain_selection_indices = [i for i, j in enumerate(captain_selection) if j == 1]
	captain_selection_elements = player_elements[captain_selection_indices]
	# get bench elements
	bench_selection = [int(round(j)) for j in bench.value]
	bench_selection_indices = [i for i, j in enumerate(bench_selection) if j == 1]
	bench_selection_elements = player_elements[bench_selection_indices]

	return first_team_selection_elements, captain_selection_elements, bench_selection_elements


def calculate_team_total_points(
		df,
		first_team_elements,
		bench_elements,
		event,
		num_transfers=0,
		carried_over_transfers=0
):
	df = df.copy()
	df = df[df['event'] == event]
	df = df[df['element'].isin(list(first_team_elements) + list(bench_elements))]
	df['is_first_team'] = 0
	df.loc[df['element'].isin(list(first_team_elements)), 'is_first_team'] = 1

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
	present_bench_players = list(df[(df['minutes'] > 0) & (df['is_first_team'] == 0)]['element'])
	num_missing_players = len(missing_players)
	num_present_bench_players = len(present_bench_players)

	if num_missing_players > 0:
		num_keepers = 1
		min_defenders = 3
		min_midfielders = 2
		min_strikers = 1

		for i in range(0, min(3, num_missing_players, num_present_bench_players)):
			substitute = df[df['is_first_team'] == 0].iloc[i]['element']
			for missing_player in missing_players:
				sub_loop_df = df.copy()
				sub_loop_df.loc[sub_loop_df['element'] == substitute, 'is_first_team'] = 1
				sub_loop_df.loc[sub_loop_df['element'] == missing_player, 'is_first_team'] = 0
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
					missing_players = list(df[(df['minutes'] == 0) & (df['is_first_team'] == 1)]['element'])
					num_missing_players = len(missing_players)
					break

	transfer_cost = max(num_transfers - carried_over_transfers - 1, 0) * 4
	team_total_points = \
		sum(df[df['is_first_team'] == 1]['total_points'] * (df[df['is_first_team'] == 1]['is_captain'] + 1))

	team_predicted_total_points = \
		sum(df[df['is_first_team'] == 1]['predicted_total_points'] * (df[df['is_first_team'] == 1]['is_captain'] + 1))

	return team_total_points - transfer_cost, team_predicted_total_points, df
