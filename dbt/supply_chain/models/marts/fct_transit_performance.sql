with shipments as (
    select * from {{ ref('stg_shipments') }}
)
, carriers as (
    select
        carrier_id
        , carrier_name
        , on_time_reliability
    from {{ ref('stg_carriers') }}
)
, enriched as (
    select
        shipments.shipment_id
        , shipments.order_id
        , shipments.carrier_id
        , carriers.carrier_name
        , shipments.warehouse_id
        , shipments.store_id
        , shipments.ship_date
        , shipments.promised_delivery_date
        , shipments.actual_delivery_date
        , shipments.distance_km
        , (shipments.actual_delivery_date <= shipments.promised_delivery_date) as is_on_time
        , {{ dbt.datediff('shipments.promised_delivery_date', 'shipments.actual_delivery_date', 'day') }} as delay_days -- noqa: LT05
    from shipments
    left join carriers
        on shipments.carrier_id = carriers.carrier_id
)
select
    shipment_id
    , order_id
    , carrier_id
    , carrier_name
    , warehouse_id
    , store_id
    , ship_date
    , promised_delivery_date
    , actual_delivery_date
    , distance_km
    , is_on_time
    , delay_days
from enriched
