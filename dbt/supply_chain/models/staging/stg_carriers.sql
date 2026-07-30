{{ config(tags=['static']) }}

with source as (
    select * from {{ source('raw', 'carriers') }}
)
, renamed as (
    select
        carrier_id::integer as carrier_id
        , carrier_name::text as carrier_name
        , on_time_reliability::numeric(5,3) as on_time_reliability
    from source
)
, deduped as (
    select
        *
        , row_number() over (
            partition by carrier_id
            order by carrier_id
        ) as row_num
    from renamed
)
select
    carrier_id
    , carrier_name
    , on_time_reliability
from deduped
where row_num = 1