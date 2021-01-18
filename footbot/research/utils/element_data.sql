-- element data for a given season and event
-- this data is used by the team selector
SELECT
  e.element_all,
  e.safe_web_name,
  e.element_type,
  e.team,
  e.value
FROM (
  SELECT
    *,
    -- find the most recent data for each element, across all events
    ROW_NUMBER() OVER(PARTITION BY element_all ORDER BY ts DESC) _is_recent
  FROM (
    -- get element data from element_data
    -- this table contains elements, even if they have no fixtures
    -- this table is only populated for 1920 event 4 onwards
    SELECT
      element_all,
      e.safe_web_name,
      ed.element_type,
      ed.team,
      now_cost AS value,
      datetime AS ts
    FROM
      `footbot-001.fpl.element_data_all` AS ed
    INNER JOIN
      `footbot-001.fpl.elements_all` AS e
    ON
      ed.element = e.element
      AND e.season = '{season}'
    WHERE
      (current_event + 1 <= {event}
        AND ed.season = '{season}')
      OR (ed.season < '{season}')
    UNION ALL
    -- fall back to element_gameweeks table
    -- this table does not contain elements if they have no fixtures
    -- this table is populated for all seasons
    SELECT
      element_all,
      safe_web_name,
      element_type,
      team,
      value,
      eg.kickoff_time AS ts
    FROM
      `footbot-001.fpl.element_gameweeks_all` AS eg
    INNER JOIN
      `footbot-001.fpl.elements_all` AS e
    ON
      eg.element = e.element
      AND eg.season = e.season
    WHERE
      (event <= {event}
        AND eg.season = '{season}')
      OR (eg.season < '{season}') ) ) AS e
-- only include elements from season of interest
INNER JOIN (
  SELECT
    DISTINCT element_all
  FROM
    `footbot-001.fpl.elements_all`
  WHERE
    season = '{season}' ) AS s
ON
  e.element_all = s.element_all
WHERE
  _is_recent = 1 -- deduplicate by taking most recent data for each element