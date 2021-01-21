-- total points earned and minutes played by event, element for a given season
-- this is used to calculate the points earned by selected players
-- minutes is required when making substitutions
-- this data does not contain elements without fixtures
SELECT
  event,
  element_all,
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
  eg.season = '{season}'
GROUP BY
  1,
  2