ALTER TABLE nycdb.main.annualized_sales ADD COLUMN bbl VARCHAR;

UPDATE nycdb.main.annualized_sales
SET bbl = borough || LPAD(block, 5, '0') || LPAD(lot, 4, '0');


CREATE OR REPLACE TABLE aggregated_dof_sales AS
SELECT
    bbl,
    ZipCode as zip_code,
    ResidentialUnits as residential_units,
    CommercialUnits as commercial_units,
    TotalUnits as total_units,
    LandSquareFeet as land_square_feet,
    YearBuilt as year_built,
    SalePrice as sale_price,
    SaleDate as sale_date,
    GrossSquareFeet as gross_square_feet,
FROM nycdb.main.dof_sales

UNION ALL

SELECT
    bbl,
    zip_code,
    residential_units,
    commercial_units,
    total_units,
    land_square_feet,
    year_built,
    sale_price,
    sale_date,
    gross_square_feet
FROM nycdb.main.annualized_sales;


DROP TABLE nycdb.main.dof_sales;
DROP TABLE nycdb.main.dof_annualized_sales;