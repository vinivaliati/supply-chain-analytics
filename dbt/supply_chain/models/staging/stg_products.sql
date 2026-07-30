{{ config(tags=['static']) }}

with source as (
    select * from {{ source('raw', 'products') }}
)
, renamed as (
    select
        sku_id::integer as sku_id
        , sku_name::text as sku_name
        , category::text as category
        , supplier_id::integer as supplier_id
        , unit_cost::numeric(10,2) as unit_cost
        , weight_kg::numeric(10,2) as weight_kg
        , abc_curve::text as abc_curve
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