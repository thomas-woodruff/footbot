import pandas as pd

from footbot.research.utils.simulator import aggregate_predictions
from footbot.research.utils.simulator import get_team_selector_input
from footbot.research.utils.simulator import set_event_state


def test_aggregate_predictions():
    predictions_df = pd.DataFrame(
        [
            {"element_all": 1, "event": 1, "predicted_total_points": 1.0},
            {"element_all": 1, "event": 2, "predicted_total_points": 2.0},
            {"element_all": 1, "event": 3, "predicted_total_points": 3.0},
            {"element_all": 2, "event": 1, "predicted_total_points": 1.0},
            {"element_all": 2, "event": 2, "predicted_total_points": 2.0},
            {"element_all": 2, "event": 4, "predicted_total_points": 3.0},
            {"element_all": 3, "event": 1, "predicted_total_points": 1.0},
            {"element_all": 3, "event": 2, "predicted_total_points": 2.0},
            {"element_all": 3, "event": 2, "predicted_total_points": 3.0},
            {"element_all": 3, "event": 3, "predicted_total_points": 3.0},
        ]
    )

    df = aggregate_predictions(predictions_df, 1, 3)

    expected_df = pd.DataFrame(
        [
            {"element_all": 1, "avg_predicted_total_points": 2.0},
            {"element_all": 2, "avg_predicted_total_points": 1.0},
            {"element_all": 3, "avg_predicted_total_points": 3.0},
        ]
    )

    pd.testing.assert_frame_equal(df, expected_df)


def test_get_team_selector_input():
    predictions_df = pd.DataFrame(
        [{"element_all": 1, "event": 1, "predicted_total_points": 1.0}]
    )

    element_data_df = pd.DataFrame(
        [
            {"element_all": 1, "element_type": 1, "team": 1, "value": 10.0},
            {"element_all": 2, "element_type": 4, "team": 3, "value": 7.5},
        ]
    )

    players = get_team_selector_input(predictions_df, element_data_df, 1, 1)

    expected_players = [
        {
            "element": 1,
            "element_type": 1,
            "team": 1,
            "value": 10.0,
            "avg_predicted_total_points": 1.0,
        },
        {
            "element": 2,
            "element_type": 4,
            "team": 3,
            "value": 7.5,
            "avg_predicted_total_points": 0.0,
        },
    ]

    assert players == expected_players


def test_set_event_state():

    element_data_df = pd.DataFrame(
        [
            {"element_all": 1, "value": 60},
            {"element_all": 2, "value": 60},
            {"element_all": 3, "value": 60},
            {"element_all": 4, "value": 60},
            {"element_all": 5, "value": 60},
            {"element_all": 6, "value": 60},
            {"element_all": 7, "value": 60},
            {"element_all": 8, "value": 60},
            {"element_all": 9, "value": 60},
            {"element_all": 10, "value": 60},
            {"element_all": 11, "value": 60},
            {"element_all": 12, "value": 60},
            {"element_all": 13, "value": 60},
            {"element_all": 14, "value": 60},
            {"element_all": 15, "value": 60},
        ]
    )

    assert set_event_state(1, None, None, None, None, element_data_df) == {
        "existing_squad_elements": None,
        "total_budget": 1000,
        "free_transfers_available": 1,
    }

    assert set_event_state(
        2,
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
        [12, 13, 14, 15],
        100,
        1,
        element_data_df,
    ) == {
        "existing_squad_elements": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
        "total_budget": 1000,
        "free_transfers_available": 1,
    }

    assert set_event_state(
        2,
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
        [12, 13, 14, 15],
        100,
        0,
        element_data_df,
    ) == {
        "existing_squad_elements": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
        "total_budget": 1000,
        "free_transfers_available": 2,
    }

    assert set_event_state(
        2,
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
        [12, 13, 14, 15],
        100,
        10,
        element_data_df,
    ) == {
        "existing_squad_elements": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
        "total_budget": 1000,
        "free_transfers_available": 1,
    }
