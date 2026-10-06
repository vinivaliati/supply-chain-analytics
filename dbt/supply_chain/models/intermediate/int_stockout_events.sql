{{ config(tags=['daily']) }}
with sales_orders as (
    select * from {{ ref('stg_sales_orders') }}
)
, inventory_coverage as (
    select * from {{ ref('int_inventory_coverage') }}
)
, stockouts as (
    select
        sales_orders.order_id
        , sales_orders.sku_id
        , sales_orders.store_id
        , sales_orders.warehouse_id
        , sales_orders.order_date
        , sales_orders.requested_qty
        , sales_orders.fulfilled_qty
        , (sales_orders.requested_qty - sales_orders.fulfilled_qty) as lost_units
        , (sales_orders.fulfilled_qty = 0) as is_total_stockout
    from sales_orders
    where sales_orders.fulfilled_qty < sales_orders.requested_qty
)
, enriched as (
    select
        stockouts.*
        , inventory_coverage.physical_stock_projected as stock_at_order_date
        , inventory_coverage.theoretical_stock as theoretical_stock_at_order_date
        , inventory_coverage.curve
        , inventory_coverage.is_below_safety_stock
        , inventory_coverage.is_below_reorder_point
    from stockouts
    left join inventory_coverage
        on stockouts.sku_id = inventory_coverage.sku_id
        and stockouts.warehouse_id = inventory_coverage.warehouse_id
        and stockouts.order_date = inventory_coverage.snapshot_date
)
select
    order_id
    , sku_id
    , store_id
    , warehouse_id
    , order_date
    , requested_qty
    , fulfilled_qty
    , lost_units
    , is_total_stockout
    , stock_at_order_date
    , theoretical_stock_at_order_date
    , curve
    , is_below_safety_stock
    , is_below_reorder_point
from enriched