{{
    config(
        materialized='incremental',
        unique_key=['snapshot_date', 'sku_id', 'warehouse_id'],
        incremental_strategy='delete+insert',
        tags=['daily']
    )
}}
with source as (
    select * from {{ source('raw', 'inventory_snapshots') }}
)
, renamed as (
    select
        snapshot_date::date as snapshot_date
        , sku_id::integer as sku_id
        , warehouse_id::integer as warehouse_id
        , theoretical_stock::integer as theoretical_stock
        , physical_stock::integer as physical_stock
        , safety_stock::integer as safety_stock
        , reorder_point::integer as reorder_point
        , in_transit_qty::integer as in_transit_qty
        , avg_daily_demand::numeric(10, 2) as avg_daily_demand
        , curve::text as curve
        , is_counted::boolean as is_counted
    from source
)
select
    snapshot_date
    , sku_id
    , warehouse_id
    , theoretical_stock
    , physical_stock
    , safety_stock
    , reorder_point
    , in_transit_qty
    , avg_daily_demand
    , curve
    , is_counted
from renamed

{% if is_incremental() %}
    where snapshot_date > (select max(snapshot_date) from {{ this }})
{% endif %}
