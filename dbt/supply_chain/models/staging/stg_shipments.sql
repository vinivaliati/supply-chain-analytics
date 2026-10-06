{{ config(tags=['daily']) }}

with source as (
    select * from {{ source('raw', 'shipments') }}
)
, renamed as (
    select
        shipment_id::integer as shipment_id
        , order_id::integer as order_id
        , carrier_id::integer as carrier_id
        , warehouse_id::integer as warehouse_id
        , store_id::integer as store_id
        , ship_date::date as ship_date
        , promised_delivery_date::date as promised_delivery_date
        , actual_delivery_date::date as actual_delivery_date
        , distance_km::numeric(10,1) as distance_km
    from source
)
, deduped as (
    select
        *
        , row_number() over (
            partition by shipment_id
            order by shipment_id
        ) as row_num
    from renamed
)
select
    shipment_id
    , order_id
    , carrier_id
    , warehouse_id
    , store_id
    , ship_date
    , promised_delivery_date
    , actual_delivery_date
    , distance_km
from deduped
where row_num = 1