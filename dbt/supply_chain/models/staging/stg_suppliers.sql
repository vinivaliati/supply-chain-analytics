{{ config(tags=['static']) }}

with source as (
    select * from {{ source('raw', 'suppliers') }}
)
, renamed as (
    select
        cast(supplier_id as {{ dbt.type_int() }}) as supplier_id
        , cast(supplier_name as {{ dbt.type_string() }}) as supplier_name
        , cast(region as {{ dbt.type_string() }}) as region
        , cast(reliability_score as {{ dbt.type_numeric() }}) as reliability_score
        , cast(promised_lead_time_days as {{ dbt.type_int() }}) as promised_lead_time_days
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
