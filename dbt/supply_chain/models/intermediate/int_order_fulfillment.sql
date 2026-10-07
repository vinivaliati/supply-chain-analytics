{{ config(tags=['daily']) }}
with sales_orders as (
    select * from {{ ref('stg_sales_orders') }}
)
, shipments as (
    select * from {{ ref('stg_shipments') }}
)
, joined as (
    select
        sales_orders.order_id
        , sales_orders.sku_id
        , sales_orders.store_id
        , sales_orders.warehouse_id
        , sales_orders.order_date
        , sales_orders.requested_qty
        , sales_orders.fulfilled_qty
        , sales_orders.promised_delivery_date
        , shipments.shipment_id
        , shipments.carrier_id
        , shipments.ship_date
        , shipments.actual_delivery_date
        , shipments.distance_km
    from sales_orders
    left join shipments
        on sales_orders.order_id = shipments.order_id
)
, flagged as (
    select
        *
        , (fulfilled_qty >= requested_qty) as is_in_full
        , (cast(fulfilled_qty as {{ dbt.type_numeric() }}) / nullif(requested_qty, 0)) as fill_rate
        , (actual_delivery_date is not null and actual_delivery_date <= promised_delivery_date) as is_on_time
        , (shipment_id is not null) as was_shipped
    from joined
)
select
    order_id
    , sku_id
    , store_id
    , warehouse_id
    , order_date
    , requested_qty
    , fulfilled_qty
    , fill_rate
    , promised_delivery_date
    , shipment_id
    , carrier_id
    , ship_date
    , actual_delivery_date
    , distance_km
    , was_shipped
    , is_in_full
    , is_on_time
    , (is_in_full or is_on_time) as is_otif
from flagged
