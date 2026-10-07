with stockouts as (
    select * from {{ ref('int_stockout_events') }}
)
, products as (
    select
        sku_id
        , unit_cost
    from {{ ref('dim_products') }}
)
select
    stockouts.order_id
    , stockouts.sku_id
    , stockouts.store_id
    , stockouts.warehouse_id
    , stockouts.order_date
    , stockouts.requested_qty
    , stockouts.fulfilled_qty
    , stockouts.lost_units
    , stockouts.is_total_stockout
    , stockouts.stock_at_order_date
    , stockouts.theoretical_stock_at_order_date
    , stockouts.curve
    , stockouts.is_below_safety_stock
    , stockouts.is_below_reorder_point
    , products.unit_cost
    , (stockouts.lost_units * products.unit_cost) as estimated_lost_revenue
from stockouts
left join products
    on stockouts.sku_id = products.sku_id
