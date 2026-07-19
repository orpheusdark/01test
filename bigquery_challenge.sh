#!/bin/bash

set -e

PROJECT_ID=$(gcloud config get-value project)

echo "=============================="
echo "Starting Challenge Lab"
echo "Project: $PROJECT_ID"
echo "=============================="

#########################################
# Task 1
#########################################

echo "Creating dataset..."

bq show ${PROJECT_ID}:covid >/dev/null 2>&1 || \
bq --location=US mk -d ${PROJECT_ID}:covid

echo "Creating partitioned table..."

bq query --use_legacy_sql=false "

CREATE OR REPLACE TABLE \`${PROJECT_ID}.covid.oxford_policy_tracker\`
(
LIKE \`bigquery-public-data.covid19_govt_response.oxford_policy_tracker\`
)
PARTITION BY date
OPTIONS(
partition_expiration_days=2175
);

"

echo "Loading data..."

bq query --use_legacy_sql=false "

INSERT INTO \`${PROJECT_ID}.covid.oxford_policy_tracker\`

SELECT *

FROM \`bigquery-public-data.covid19_govt_response.oxford_policy_tracker\`

WHERE alpha_3_code NOT IN ('GBR','BRA','CAN','USA');

"

#########################################
# Task 2
#########################################

echo "Updating schema..."

bq query --use_legacy_sql=false "

ALTER TABLE \`${PROJECT_ID}.covid_data.global_mobility_tracker_data\`

ADD COLUMN population INT64,
ADD COLUMN country_area FLOAT64,
ADD COLUMN mobility STRUCT<
    avg_retail FLOAT64,
    avg_grocery FLOAT64,
    avg_parks FLOAT64,
    avg_transit FLOAT64,
    avg_workplace FLOAT64,
    avg_residential FLOAT64
>;

"

#########################################
# Task 3
#########################################

echo "Updating population..."

bq query --use_legacy_sql=false "

UPDATE
\`${PROJECT_ID}.covid_data.consolidate_covid_tracker_data\` t

SET population = p.pop_data_2019

FROM (

SELECT DISTINCT
country_territory_code,
pop_data_2019

FROM
\`bigquery-public-data.covid19_ecdc.covid_19_geographic_distribution_worldwide\`

) p

WHERE t.alpha_3_code = p.country_territory_code;

"

#########################################
# Task 4
#########################################

echo "Updating country area..."

bq query --use_legacy_sql=false "

UPDATE
\`${PROJECT_ID}.covid_data.consolidate_covid_tracker_data\` t

SET country_area = a.country_area

FROM
\`bigquery-public-data.census_bureau_international.country_names_area\` a

WHERE t.country_name = a.country_name;

"

#########################################
# Bonus (Required in many lab versions)
#########################################

echo "Updating mobility data..."

bq query --use_legacy_sql=false "

UPDATE
\`${PROJECT_ID}.covid_data.consolidate_covid_tracker_data\` t

SET mobility = STRUCT(
m.avg_retail,
m.avg_grocery,
m.avg_parks,
m.avg_transit,
m.avg_workplace,
m.avg_residential
)

FROM (

SELECT
country_region,
date,

AVG(retail_and_recreation_percent_change_from_baseline) AS avg_retail,
AVG(grocery_and_pharmacy_percent_change_from_baseline) AS avg_grocery,
AVG(parks_percent_change_from_baseline) AS avg_parks,
AVG(transit_stations_percent_change_from_baseline) AS avg_transit,
AVG(workplaces_percent_change_from_baseline) AS avg_workplace,
AVG(residential_percent_change_from_baseline) AS avg_residential

FROM
\`bigquery-public-data.covid19_google_mobility.mobility_report\`

GROUP BY
country_region,
date

) m

WHERE
t.country_name = m.country_region
AND t.date = m.date;

"

echo
echo "======================================"
echo "All required tasks completed."
echo "======================================"
