select
    cast(supplier_id as {{ dbt.type_int() }}) as supplier_id
    , cast(supplier_name as {{ dbt.type_string() }}) as supplier_name
    , cast(region as {{ dbt.type_string() }}) as region
    , cast(reliability_score as {{ dbt.type_numeric() }}) as reliability_score
    , cast(promised_lead_time_days as {{ dbt.type_int() }}) as promised_lead_time_days
from {{ source('raw', 'suppliers') }}
