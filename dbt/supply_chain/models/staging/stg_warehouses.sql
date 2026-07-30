{{ config(tags=['static']) }}

with source as (
    select * from {{ source('raw', 'warehouses') }}
)
, renamed as (
    select
        warehouse_id::integer as warehouse_id
        , warehouse_name::text as warehouse_name
        , region::text as region
        , capacity_units::integer as capacity_units
    from source
)
, deduped as (
    select
        *
        , row_number() over (
            partition by warehouse_id
            order by warehouse_id
        ) as row_num
    from renamed
)
select
    warehouse_id
    , warehouse_name
    , region
    , capacity_units
from deduped
where row_num = 1