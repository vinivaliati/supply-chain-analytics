{{ config(tags=['daily']) }}
with inventory as (
    select * from {{ ref('stg_inventory_snapshots') }}
)
, with_count_group as (
    select
        *
        , sum(case when is_counted then 1 else 0 end) over (
            partition by sku_id, warehouse_id
            order by snapshot_date
            rows between unbounded preceding and current row
        ) as count_group
    from inventory
)
, with_last_known_physical as (
    select
        *
        , max(case when is_counted then physical_stock end) over (
            partition by sku_id, warehouse_id, count_group
        ) as last_known_physical_stock
        , max(case when is_counted then theoretical_stock end) over (
            partition by sku_id, warehouse_id, count_group
        ) as theoretical_stock_at_last_count
    from with_count_group
)
, projected as (
    select
        snapshot_date
        , sku_id
        , warehouse_id
        , theoretical_stock
        , physical_stock as physical_stock_actual
        , is_counted
        , curve
        , safety_stock
        , reorder_point
        , in_transit_qty
        , avg_daily_demand
        , last_known_physical_stock
        , coalesce(
            last_known_physical_stock + (theoretical_stock - theoretical_stock_at_last_count)
            , theoretical_stock
        ) as physical_stock_projected_raw
    from with_last_known_physical
)
select
    snapshot_date
    , sku_id
    , warehouse_id
    , theoretical_stock
    , physical_stock_actual
    , physical_stock_projected_raw
    , greatest(physical_stock_projected_raw, 0) as physical_stock_projected
    , is_counted
    , curve
    , safety_stock
    , reorder_point
    , in_transit_qty
    , avg_daily_demand
    , (physical_stock_projected_raw < 0) as projection_went_negative
    , (greatest(physical_stock_projected_raw, 0) - theoretical_stock) as physical_vs_theoretical_divergence
from projected