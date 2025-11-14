DROP MACRO IF EXISTS normalize_property_address;

CREATE OR REPLACE MACRO normalize_property_address(street_number, street_name, borough) AS (
   --params
    WITH inputs AS (
        SELECT
            street_number AS orig_number,
            street_name AS orig_name,
            borough AS b
    ),
    cleaned AS (
        SELECT
            CASE
                WHEN orig_number = ''
                     AND regexp_full_match(orig_name, '^[0-9]+[A-Za-z].*')
                    THEN regexp_extract(orig_name, '^([0-9]+).*', 1)
                ELSE regexp_replace(orig_number, '[^0-9]', '', 'g')
            END AS clean_number,
            CASE
                WHEN orig_number = ''
                     AND regexp_full_match(orig_name, '^[0-9]+[A-Za-z].*')
                    THEN regexp_replace(orig_name, '^[0-9]+(.*)$', '\1')
                ELSE orig_name
            --returns sname
            END AS sname,
            b
        FROM inputs
    ),
    formatted AS (
        SELECT
            CASE
                WHEN b = 4
                     AND length(clean_number) >= 2
                     AND position('-' IN clean_number) = 0
                    THEN substring(clean_number, 1, length(clean_number) - 2)
                         || '-' || right(clean_number, 2)
                ELSE clean_number
            --returns formatted_number
            END AS formatted_number,
            sname
        FROM cleaned
    ),
    directional AS (
        SELECT
            formatted_number,
            CASE
                WHEN sname ILIKE 'E %' OR sname ILIKE 'EAST %' THEN 'east'
                WHEN sname ILIKE 'W %' OR sname ILIKE 'WEST %' THEN 'west'
                WHEN sname ILIKE 'N %' OR sname ILIKE 'NORTH %' THEN 'north'
                WHEN sname ILIKE 'S %' OR sname ILIKE 'SOUTH %' THEN 'south'
                ELSE ''
            END AS direction,
            CASE
                WHEN sname ILIKE 'E %' OR sname ILIKE 'EAST %'
                  OR sname ILIKE 'W %' OR sname ILIKE 'WEST %'
                  OR sname ILIKE 'N %' OR sname ILIKE 'NORTH %'
                  OR sname ILIKE 'S %' OR sname ILIKE 'SOUTH %'
                THEN regexp_replace(sname, '^(E|EAST|W|WEST|N|NORTH|S|SOUTH)\s+', '', 'i')
                ELSE sname
--             returns sname_no_direction
            END AS sname_no_direction
        FROM formatted
    ),
    parsed AS (
        SELECT
            formatted_number,
            direction,
            sname_no_direction AS sname,
            lower(sname_no_direction) AS lower_sname
        FROM directional
    ),
    street_type_extracted AS (
        SELECT
            formatted_number,
            direction,
            sname,
            lower_sname,
            CASE
                WHEN sname ILIKE '%ROAD' OR sname ILIKE '% ROAD%'
                  OR sname ILIKE '%RD' OR sname ILIKE '% RD%' THEN 'road'
                WHEN sname ILIKE '%STREET' OR sname ILIKE '% STREET%'
                  OR sname ILIKE '%ST' OR sname ILIKE '% ST%' THEN 'street'
                WHEN sname ILIKE '%AVENUE' OR sname ILIKE '% AVENUE%'
                  OR sname ILIKE '%AVE' OR sname ILIKE '% AVE%' THEN 'avenue'
                WHEN sname ILIKE '%PLACE' OR sname ILIKE '% PLACE%'
                  OR sname ILIKE '%PL' OR sname ILIKE '% PL%' THEN 'place'
                WHEN sname ILIKE '%DRIVE' OR sname ILIKE '% DRIVE%'
                  OR sname ILIKE '%DR' OR sname ILIKE '% DR%' THEN 'drive'
                WHEN sname ILIKE '%TERRACE' OR sname ILIKE '% TERRACE%'
                  OR sname ILIKE '%TER' OR sname ILIKE '% TER%' THEN 'terrace'
                ELSE ''
            END AS street_type,
            regexp_replace(
                lower_sname,
                '\s*(road|rd|street|st|avenue|ave|place|pl|drive|dr|terrace|ter)\s*$',
                '',
                'i'
            ) AS base_name
        FROM parsed
    ),
    final AS (
        SELECT
            formatted_number,
            direction,
            sname,
            base_name,
            street_type,
            CASE
                WHEN base_name LIKE '%st'
                  OR base_name LIKE '%nd'
                  OR base_name LIKE '%rd'
                  OR base_name LIKE '%th'
                THEN true
                ELSE false
            END AS has_ordinal,
            regexp_extract(base_name, '^([0-9]+)', 1) AS number_part
        FROM street_type_extracted
    )
    SELECT
        formatted_number || ' ' ||
        CASE
            WHEN number_part <> '' AND number_part IS NOT NULL THEN
                (CASE WHEN direction <> '' THEN direction || ' ' ELSE '' END) ||
                CASE
                    WHEN has_ordinal THEN regexp_extract(base_name, '^([0-9]+(st|nd|rd|th))', 1)
                    ELSE
                        number_part ||
                        (CASE
                            WHEN right(number_part, 2) IN ('11', '12', '13') THEN 'th'
                            WHEN right(number_part, 1) = '1' THEN 'st'
                            WHEN right(number_part, 1) = '2' THEN 'nd'
                            WHEN right(number_part, 1) = '3' THEN 'rd'
                            ELSE 'th'
                        END)
                END ||
                (CASE WHEN street_type <> '' THEN ' ' || street_type ELSE '' END)
            ELSE
                base_name ||
                (CASE WHEN street_type <> '' THEN ' ' || street_type ELSE '' END)
        END
    FROM final
);
