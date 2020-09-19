WITH
  predictions AS (
  SELECT
    element,
    SUM(predicted_total_points)/({end_event} - {start_event} + 1) AS average_points
  FROM (
    SELECT
      element,
      event,
      predicted_total_points
    FROM
      `footbot-001.fpl.element_gameweeks_predictions_2021_v01` )
  WHERE
    event BETWEEN {start_event}
    AND {end_event}
  GROUP BY
    1 ),
  --------------------------------------------------------------------------------------------------------------------------------------------------------------
  elements AS (
  SELECT
    element,
    element_type,
    now_cost AS value,
    team,
    safe_web_name,
    prob_playing
  FROM (
    SELECT
      element,
      element_type,
      now_cost,
      team,
      safe_web_name,
      COALESCE(chance_of_playing_next_round,
        100)/100 AS prob_playing,
      ROW_NUMBER() OVER(PARTITION BY element ORDER BY datetime DESC) AS is_current,
    FROM
      `footbot-001.fpl.element_data_2021` )
  WHERE
    is_current = 1 )
  --------------------------------------------------------------------------------------------------------------------------------------------------------------
  --------------------------------------------------------------------------------------------------------------------------------------------------------------
  --------------------------------------------------------------------------------------------------------------------------------------------------------------
SELECT
  e.element,
  element_type,
  value,
  team,
  COALESCE(average_points * prob_playing, 0) AS average_points,
  safe_web_name
FROM
  elements AS e
LEFT JOIN
  predictions AS p
ON
  e.element = p.element
ORDER BY
  5 DESC