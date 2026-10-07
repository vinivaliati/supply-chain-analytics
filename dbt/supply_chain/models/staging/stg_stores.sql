{{ config(tags=['static']) }}

with source as (
    select * from {{ source('raw', 'stores') }}
)
, renamed as (
    select
        store_id::integer as store_id
        , store_name::text as store_name
        , region::text as region
        , warehouse_id::integer as warehouse_id
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
