select
    cast(store_id as {{ dbt.type_int() }}) as store_id
    , cast(store_name as {{ dbt.type_string() }}) as store_name
    , cast(region as {{ dbt.type_string() }}) as region
    , cast(warehouse_id as {{ dbt.type_int() }}) as warehouse_id
from {{ source('raw', 'stores') }}
