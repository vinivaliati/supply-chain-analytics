select
    cast(carrier_id as {{ dbt.type_int() }}) as carrier_id
    , cast(carrier_name as {{ dbt.type_string() }}) as carrier_name
    , cast(on_time_reliability as {{ dbt.type_numeric() }}) as on_time_reliability
from {{ source('raw', 'carriers') }}
