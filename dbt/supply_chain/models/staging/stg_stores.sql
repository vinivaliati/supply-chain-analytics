{{ config(tags=['static']) }}

with source as (
    select * from {{ source('raw', 'stores') }}
)
, renamed as (
    select
        cast(store_id as {{ dbt.type_int() }}) as store_id
        , cast(store_name as {{ dbt.type_string() }}) as store_name
        , cast(region as {{ dbt.type_string() }}) as region
        , cast(warehouse_id as {{ dbt.type_int() }}) as warehouse_id
    from source
)
, deduped as (
    select
        *
        , row_number() over (
            partition by store_id
            order by store_id
        ) as row_num
    from renamed
)
select
    store_id
    , store_name
    , region
    , warehouse_id
from deduped
where row_num = 1
