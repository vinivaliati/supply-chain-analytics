{{ config(tags=['daily']) }}
select
    po_id
    , supplier_id
    , sku_id
    , warehouse_id
    , order_date
    , promised_date
    , received_date
    , ordered_qty
    , received_qty
    , (received_qty >= ordered_qty) as is_in_full
    , (received_date <= promised_date) as is_on_time
    , (received_qty >= ordered_qty and received_date <= promised_date) as is_otif
from {{ ref('stg_purchase_orders') }}
