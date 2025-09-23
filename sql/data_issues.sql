
-- rows with no address
select search_prop_address, count(*)
from aggregated_acris_records
group by search_prop_address
order by  count(*) DESC
    limit 1000

select count(*)
from aggregated_acris_records
where aggregated_acris_records.search_prop_address is null
--and prop_type !='PRE-ACRIS'
  and bbl is not null
    limit 100

select *
from aggregated_acris_records
where bbl = '3048850043'
limit 100


select distinct streetnumber , streetname
from personal_property_legals a
where a.bbl in (
    SELECT distinct bbl
    FROM personal_property_legals
    where bbl is not null
      and streetnumber is  null and  streetname is null
)
  and streetnumber is not null and  streetname is not null
-- this has usefull data forthe bbl
--https://data.cityofnewyork.us/City-Government/Property-Address-Directory/bc8t-ecyu/about_data

--bbl matching to multiple addreses
SELECT bbl , count(DISTINCT search_prop_address)
FROM aggregated_acris_records vcv
GROUP BY bbl
HAVING count(DISTINCT search_prop_address) > 1
    LIMIT 100;


SELECT search_prop_address ,* FROM aggregated_acris_records vcv
WHERE bbl IN ('1000110021')
ORDER BY  bbl, prop_streetnumber , src


