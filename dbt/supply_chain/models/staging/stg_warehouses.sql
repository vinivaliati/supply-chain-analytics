{{ config(tags=['static']) }}

with source as (
    select * from {{ source('raw', 'warehouses') }}
)
, renamed as (
    select
        cast(warehouse_id as {{ dbt.type_int() }}) as warehouse_id
        , cast(warehouse_name as {{ dbt.type_string() }}) as warehouse_name
        , cast(region as {{ dbt.type_string() }}) as region
        , cast(capacity_units as {{ dbt.type_int() }}) as capacity_units
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
