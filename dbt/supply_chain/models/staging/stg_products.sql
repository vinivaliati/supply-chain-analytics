{{ config(tags=['static']) }}

with source as (
    select * from {{ source('raw', 'products') }}
)
, renamed as (
    select
        cast(sku_id as {{ dbt.type_int() }}) as sku_id
        , cast(sku_name as {{ dbt.type_string() }}) as sku_name
        , cast(category as {{ dbt.type_string() }}) as category
        , cast(supplier_id as {{ dbt.type_int() }}) as supplier_id
        , cast(unit_cost as {{ dbt.type_numeric() }}) as unit_cost
        , cast(weight_kg as {{ dbt.type_numeric() }}) as weight_kg
        , cast(abc_curve as {{ dbt.type_string() }}) as abc_curve
    from source
)
, deduped as (
    select
        *
        , row_number() over (
            partition by sku_id
            order by sku_id
        ) as row_num
    from renamed
)
select
    sku_id
    , sku_name
    , category
    , supplier_id
    , unit_cost
    , weight_kg
    , abc_curve
from deduped
where row_num = 1
