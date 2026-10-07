{{ config(tags=['static']) }}

with source as (
    select * from {{ source('raw', 'carriers') }}
)
, renamed as (
    select
        cast(carrier_id as {{ dbt.type_int() }}) as carrier_id
        , cast(carrier_name as {{ dbt.type_string() }}) as carrier_name
        , cast(on_time_reliability as {{ dbt.type_numeric() }}) as on_time_reliability
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
