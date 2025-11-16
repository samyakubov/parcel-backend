
select distinct streetnumber , streetname
from personal_property_legals a
where a.bbl in (
    SELECT distinct bbl
    FROM personal_property_legals
    where bbl is not null
      and streetnumber is  null and  streetname is null
) and streetnumber is not null and  streetname is not null
-- this has useful data for the bbl
--https://data.cityofnewyork.us/City-Government/Property-Address-Directory/bc8t-ecyu/about_data


--Has needs to be accounted for in standardization function: 13-16 BELL BOULEVA ROAD
SELECT search_prop_address , * FROM nycdb.main.aggregated_acris_records vcv
WHERE bbl IN ('4058570002')
ORDER BY  bbl, prop_streetnumber


--trying to figure out the pattern on why there are multiple addresses on one bbl
SELECT bbl , count(DISTINCT search_prop_address)
FROM nycdb.main.aggregated_acris_records vcv
where vcv.prop_type != 'OFFICE BUILDING'
and vcv.prop_type != 'COMMERCIAL REAL ESTATE'
and vcv.prop_type != 'PRE-ACRIS'
and vcv.prop_type != 'APARTMENT BUILDING'
GROUP BY bbl
HAVING count(DISTINCT search_prop_address) > 1
