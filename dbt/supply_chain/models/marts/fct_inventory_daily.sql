{{ config(materialized='incremental', unique_key=['snapshot_date', 'sku_id', 'warehouse_id']) }}
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
    , coverage_days_physical
    , coverage_days_theoretical
    , is_below_safety_stock
    , is_below_reorder_point
    , is_stockout
from {{ ref('int_inventory_coverage') }}
{% if is_incremental() %}
    where snapshot_date > (select max(loaded.snapshot_date) from {{ this }} as loaded)
{% endif %}
