DROP MACRO IF EXISTS normalize_property_address;

CREATE OR REPLACE MACRO normalize_property_address(street_number, street_name, borough) AS (
  WITH inputs AS (
    SELECT street_number AS orig_number, street_name AS orig_name, borough AS b
  ),
  cleaned AS (
    SELECT
      CASE
        WHEN orig_number = '' AND regexp_full_match(orig_name, '^[0-9]+[A-Za-z].*') THEN regexp_extract(orig_name, '^([0-9]+).*', 1)
        ELSE regexp_replace(orig_number, '[^0-9]', '', 'g')
      END AS clean_number,
      CASE
        WHEN orig_number = '' AND regexp_full_match(orig_name, '^[0-9]+[A-Za-z].*') THEN regexp_replace(orig_name, '^[0-9]+(.*)$', '\1')
        ELSE orig_name
      END AS sname,
      b
    FROM inputs
  ),
  formatted AS (
    SELECT
      CASE
        WHEN b = 4 AND length(clean_number) >= 2 AND position('-' IN clean_number) = 0
          THEN substring(clean_number, 1, length(clean_number)-2) || '-' || right(clean_number, 2)
        ELSE clean_number
      END AS formatted_number,
      sname
    FROM cleaned
  ),
  final AS (
    SELECT formatted_number, sname, regexp_replace(lower(sname), '[^0-9]', '', 'g') AS number_part
    FROM formatted
  )
  SELECT
    formatted_number || ' ' ||
    CASE
      WHEN number_part <> '' THEN
        number_part ||
        (CASE WHEN number_part ~ '11$|12$|13$' THEN 'th'
              WHEN number_part ~ '1$' THEN 'st'
              WHEN number_part ~ '2$' THEN 'nd'
              WHEN number_part ~ '3$' THEN 'rd'
              ELSE 'th' END) ||
        (CASE WHEN sname ILIKE '%ROAD' OR sname ILIKE '% RD' THEN ' road'
              WHEN sname ILIKE '%STREET' OR sname ILIKE '% ST' THEN ' street'
              WHEN sname ILIKE '%AVENUE' OR sname ILIKE '% AVE' THEN ' avenue'
              WHEN sname ILIKE '%PLACE' OR sname ILIKE '% PL' THEN ' place'
              WHEN sname ILIKE '%DRIVE' OR sname ILIKE '% DR' THEN ' drive'
              WHEN sname ILIKE '%TERRACE' OR sname ILIKE '% TER' THEN ' terrace'
              ELSE '' END)
      ELSE lower(sname)
    END
  FROM final
);