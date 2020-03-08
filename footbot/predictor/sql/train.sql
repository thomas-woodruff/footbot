SELECT
  * EXCEPT(goals_scored,
    assists,
    clean_sheets,
    goals_conceded,
    saves,
    minutes,
    element,
    element_all,
    safe_web_name,
    event,
    event_all,
    season,
    fixture )
FROM
  `footbot-001.fpl.element_gameweeks_features_all_v01`
WHERE
  rolling_avg_minutes_element_p10 >= 45