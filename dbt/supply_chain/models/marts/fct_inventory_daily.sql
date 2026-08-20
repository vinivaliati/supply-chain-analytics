{{ config(tags=['daily']) }}
select
    snapshot_date
    , sku_id
    , warehouse_id
    , theoretical_stock
    , physical_stock_projected
    , safety_stock
    , reorder_point
    , in_transit_qty
    , avg_daily_demand
    , curve
    , coverage_days_physical
    , coverage_days_theoretical
    , is_below_safety_stock
    , is_below_reorder_point
    , is_stockout
from {{ ref('int_inventory_coverage') }}