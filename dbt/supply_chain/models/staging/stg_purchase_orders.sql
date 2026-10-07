{{ config(tags=['daily']) }}

with source as (
    select * from {{ source('raw', 'purchase_orders') }}
)
, renamed as (
    select
        cast(po_id as {{ dbt.type_int() }}) as po_id
        , cast(supplier_id as {{ dbt.type_int() }}) as supplier_id
        , cast(sku_id as {{ dbt.type_int() }}) as sku_id
        , cast(warehouse_id as {{ dbt.type_int() }}) as warehouse_id
        , cast(order_date as date) as order_date
        , cast(promised_date as date) as promised_date
        , cast(received_date as date) as received_date
        , cast(ordered_qty as {{ dbt.type_int() }}) as ordered_qty
        , cast(received_qty as {{ dbt.type_int() }}) as received_qty
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
