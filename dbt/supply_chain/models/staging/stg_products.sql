select
    cast(sku_id as {{ dbt.type_int() }}) as sku_id
    , cast(sku_name as {{ dbt.type_string() }}) as sku_name
    , cast(category as {{ dbt.type_string() }}) as category
    , cast(supplier_id as {{ dbt.type_int() }}) as supplier_id
    , cast(unit_cost as {{ dbt.type_numeric() }}) as unit_cost
    , cast(weight_kg as {{ dbt.type_numeric() }}) as weight_kg
    , cast(abc_curve as {{ dbt.type_string() }}) as abc_curve
from {{ source('raw', 'products') }}
