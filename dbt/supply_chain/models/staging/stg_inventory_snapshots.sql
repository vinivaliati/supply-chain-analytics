select
    cast(snapshot_date as date) as snapshot_date
    , cast(sku_id as {{ dbt.type_int() }}) as sku_id
    , cast(warehouse_id as {{ dbt.type_int() }}) as warehouse_id
    , cast(theoretical_stock as {{ dbt.type_int() }}) as theoretical_stock
    , cast(physical_stock as {{ dbt.type_int() }}) as physical_stock
    , cast(safety_stock as {{ dbt.type_int() }}) as safety_stock
    , cast(reorder_point as {{ dbt.type_int() }}) as reorder_point
    , cast(in_transit_qty as {{ dbt.type_int() }}) as in_transit_qty
    , cast(avg_daily_demand as {{ dbt.type_numeric() }}) as avg_daily_demand
    , cast(curve as {{ dbt.type_string() }}) as curve
    , cast(is_counted as {{ dbt.type_boolean() }}) as is_counted
from {{ source('raw', 'inventory_snapshots') }}
