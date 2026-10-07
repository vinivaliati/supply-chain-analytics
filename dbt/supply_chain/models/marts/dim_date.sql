{{ config(tags=['static']) }}
-- ponytail: periodo fixo, igual a START_DATE/END_DATE de data_generator/config/settings.py
with date_spine as (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2026-01-01' as date)",
        end_date="cast('2027-01-01' as date)"
    ) }}
)
select
    cast(date_day as date) as date_day
    , extract(year from date_day) as year
    , extract(quarter from date_day) as quarter
    , extract(month from date_day) as month
from date_spine
