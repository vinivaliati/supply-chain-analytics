{{ config(tags=['daily']) }}
with inventory as (
    select * from {{ ref('int_inventory_physical_projection') }}
)
, coverage as (
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
        , physical_vs_theoretical_divergence
        , (physical_stock_projected / nullif(avg_daily_demand, 0)) as coverage_days_physical
        , (theoretical_stock / nullif(avg_daily_demand, 0)) as coverage_days_theoretical
        , (physical_stock_projected <= safety_stock) as is_below_safety_stock
        , (physical_stock_projected <= reorder_point) as is_below_reorder_point
        , (physical_stock_projected <= 0) as is_stockout
    from inventory
)
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
    , physical_vs_theoretical_divergence
    , round(coverage_days_physical, 1) as coverage_days_physical
    , round(coverage_days_theoretical, 1) as coverage_days_theoretical
    , is_below_safety_stock
    , is_below_reorder_point
    , is_stockout
from coverage
