{{ config(tags=['static']) }}
with products as (
    select * from {{ ref('stg_products') }}
)
, current_curve as (
    select
        sku_id
        , abc_curve
    from {{ ref('products_abc_curve_snapshot') }}
    where dbt_valid_to is null
)
select
    products.sku_id
    , products.sku_name
    , products.category
    , products.supplier_id
    , products.unit_cost
    , products.weight_kg
    , current_curve.abc_curve
from products
left join current_curve
    on products.sku_id = current_curve.sku_id
