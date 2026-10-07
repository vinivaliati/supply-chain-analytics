{{ config(tags=['daily']) }}

with source as (
    select * from {{ source('raw', 'sales_orders') }}
)
, renamed as (
    select
        order_id::integer as order_id
        , sku_id::integer as sku_id
        , store_id::integer as store_id
        , warehouse_id::integer as warehouse_id
        , order_date::date as order_date
        , requested_qty::integer as requested_qty
        , fulfilled_qty::integer as fulfilled_qty
        , promised_delivery_date::date as promised_delivery_date
        , actual_delivery_date::date as actual_delivery_date
    from source
)
, deduped as (
    select
        *
        , row_number() over (
            partition by order_id
            order by order_id
        ) as row_num
    from renamed
)
select
    order_id
    , sku_id
    , store_id
    , warehouse_id
    , order_date
    , requested_qty
    , fulfilled_qty
    , promised_delivery_date
    , actual_delivery_date
from deduped
where row_num = 1
