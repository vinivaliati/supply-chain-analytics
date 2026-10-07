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
from {{ source('raw', 'purchase_orders') }}
