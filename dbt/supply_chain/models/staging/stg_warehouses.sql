select
    cast(warehouse_id as {{ dbt.type_int() }}) as warehouse_id
    , cast(warehouse_name as {{ dbt.type_string() }}) as warehouse_name
    , cast(region as {{ dbt.type_string() }}) as region
    , cast(capacity_units as {{ dbt.type_int() }}) as capacity_units
from {{ source('raw', 'warehouses') }}
