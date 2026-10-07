{{ config(tags=['daily']) }}

with source as (
    select * from {{ source('raw', 'shipments') }}
)
, renamed as (
    select
        cast(shipment_id as {{ dbt.type_int() }}) as shipment_id
        , cast(order_id as {{ dbt.type_int() }}) as order_id
        , cast(carrier_id as {{ dbt.type_int() }}) as carrier_id
        , cast(warehouse_id as {{ dbt.type_int() }}) as warehouse_id
        , cast(store_id as {{ dbt.type_int() }}) as store_id
        , cast(ship_date as date) as ship_date
        , cast(promised_delivery_date as date) as promised_delivery_date
        , cast(actual_delivery_date as date) as actual_delivery_date
        , cast(distance_km as {{ dbt.type_numeric() }}) as distance_km
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
