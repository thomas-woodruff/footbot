  -- element data by event, element for a given season
  -- this data is used by the team selector
DECLARE
  simulation_season STRING;
SET
  simulation_season = '{season}';
WITH
  elements AS (
  SELECT
    element_all,
    element,
    safe_web_name,
    element_type,
    team
  FROM
    `footbot-001.fpl.elements_all`
  WHERE
    season = simulation_season ),
  --------------------------------------------------------------------------------------------------------------------
  element_data AS (
    -- get element data from element_data
    -- this table contains elements, even if they have no fixtures
    -- this table is only populated for 1920 event 4 onwards
  SELECT
    season,
    current_event + 1 AS event,
    element_all,
    e.safe_web_name,
    ed.element_type,
    ed.team,
    now_cost AS value,
    datetime AS ts
  FROM
    `footbot-001.fpl.element_data_all` AS ed
  INNER JOIN
    elements AS e
  ON
    ed.element = e.element
  WHERE
    ed.season <= simulation_season ),
  --------------------------------------------------------------------------------------------------------------------
  element_gameweeks AS (
    -- get element data from element_gameweeks
    -- this table does not contain elements if they have no fixtures
    -- this table is populated for all seasons
  SELECT
    season,
    event,
    element_all,
    safe_web_name,
    element_type,
    team,
    value,
    kickoff_time AS ts
  FROM
    `footbot-001.fpl.element_gameweeks_all` AS eg
  INNER JOIN
    elements AS e
  ON
    eg.element = e.element
  WHERE
    eg.season <= simulation_season ),
  --------------------------------------------------------------------------------------------------------------------
  events AS (
  SELECT
    DISTINCT event
  FROM
    element_gameweeks
  WHERE
    season = simulation_season ),
  --------------------------------------------------------------------------------------------------------------------
  base AS (
  SELECT
    event,
    element_all
  FROM
    events
  CROSS JOIN
    elements )
  --------------------------------------------------------------------------------------------------------------------
SELECT
  event,
  element_all,
  safe_web_name,
  element_type,
  team,
  value
FROM (
    -- find the most recent data for each element, event
    -- if element has no fixtures in given event, look back to previous events
  SELECT
    b.event,
    b.element_all,
    safe_web_name,
    element_type,
    team,
    value,
    ROW_NUMBER() OVER(PARTITION BY b.event, b.element_all ORDER BY ts DESC) AS _is_most_recent
  FROM
    base AS b
  INNER JOIN (
    SELECT
      *
    FROM
      element_data
    UNION ALL
      -- fall back to element_gameweeks table
    SELECT
      *
    FROM
      element_gameweeks ) AS e
  ON
    b.element_all = e.element_all
    AND b.event >= e.event -- include all previous events
    )
WHERE
  _is_most_recent = 1