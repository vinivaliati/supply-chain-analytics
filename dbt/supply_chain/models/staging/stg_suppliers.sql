{{ config(tags=['static']) }}

with source as (
    select * from {{ source('raw', 'suppliers') }}
)
, renamed as (
    select
        supplier_id::integer as supplier_id
        , supplier_name::text as supplier_name
        , region::text as region
        , reliability_score::numeric(5,3) as reliability_score
        , promised_lead_time_days::integer as promised_lead_time_days
    from source
)
, deduped as (
    select
        *
        , row_number() over (
            partition by supplier_id
            order by supplier_id
        ) as row_num
    from renamed
)
select
    supplier_id
    , supplier_name
    , region
    , reliability_score
    , promised_lead_time_days
from deduped
where row_num = 1