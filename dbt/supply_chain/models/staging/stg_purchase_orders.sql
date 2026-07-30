{{ config(tags=['daily']) }}

with source as (
    select * from {{ source('raw', 'purchase_orders') }}
)
, renamed as (
    select
        po_id::integer as po_id
        , supplier_id::integer as supplier_id
        , sku_id::integer as sku_id
        , warehouse_id::integer as warehouse_id
        , order_date::date as order_date
        , promised_date::date as promised_date
        , received_date::date as received_date
        , ordered_qty::integer as ordered_qty
        , received_qty::integer as received_qty
    from source
)
, deduped as (
    select
        *
        , row_number() over (
            partition by po_id
            order by po_id
        ) as row_num
    from renamed
)
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
from deduped
where row_num = 1