select
    cast(order_id as {{ dbt.type_int() }}) as order_id
    , cast(sku_id as {{ dbt.type_int() }}) as sku_id
    , cast(store_id as {{ dbt.type_int() }}) as store_id
    , cast(warehouse_id as {{ dbt.type_int() }}) as warehouse_id
    , cast(order_date as date) as order_date
    , cast(requested_qty as {{ dbt.type_int() }}) as requested_qty
    , cast(fulfilled_qty as {{ dbt.type_int() }}) as fulfilled_qty
    , cast(promised_delivery_date as date) as promised_delivery_date
    , cast(actual_delivery_date as date) as actual_delivery_date
from {{ source('raw', 'sales_orders') }}
