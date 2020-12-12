-- total points earned and minutes played by element for a given season and event
-- this is used to calculate the points earned by selected players
-- minutes and element_Type are required when making substitutions
-- this data does not contain elements without fixtures
SELECT
  element_all,
  element_type,
  SUM(minutes) AS minutes,
  SUM(total_points) AS total_points
FROM
  `footbot-001.fpl.element_gameweeks_all` AS eg
INNER JOIN
  `footbot-001.fpl.elements_all` AS e
ON
  eg.element = e.element
  AND eg.season = e.season
WHERE
  event = {event}
  AND eg.season = '{season}'
GROUP BY
  1,
  2