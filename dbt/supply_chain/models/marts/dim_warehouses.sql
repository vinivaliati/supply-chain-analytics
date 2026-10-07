select
    warehouse_id
    , warehouse_name
    , region
    , capacity_units
from {{ ref('stg_warehouses') }}
