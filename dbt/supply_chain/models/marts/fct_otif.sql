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
    , is_otif
from {{ ref('int_order_fulfillment') }}
