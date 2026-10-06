{{ config(tags=['static']) }}
with date_spine as (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2024-01-01' as date)",
        end_date="cast('2025-01-01' as date)"
    ) }}
)
, enriched as (
    select
        date_day::date as date_day
        , extract(year from date_day) as year
        , extract(quarter from date_day) as quarter
        , extract(month from date_day) as month
        , to_char(date_day, 'Month') as month_name
        , extract(week from date_day) as week_of_year
        , extract(day from date_day) as day_of_month
        , extract(dow from date_day) as day_of_week
        , to_char(date_day, 'Day') as day_name
        , (extract(dow from date_day) in (0, 6)) as is_weekend
    from date_spine
)
select
    date_day
    , year
    , quarter
    , month
    , trim(month_name) as month_name
    , week_of_year
    , day_of_month
    , day_of_week
    , trim(day_name) as day_name
    , is_weekend
from enriched