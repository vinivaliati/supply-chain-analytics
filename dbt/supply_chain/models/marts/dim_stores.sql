{{ config(tags=['static']) }}
select
    stores.store_id
    , stores.store_name
    , stores.region
    , stores.warehouse_id
    , warehouses.warehouse_name
from {{ ref('stg_stores') }} as stores
left join {{ ref('stg_warehouses') }} as warehouses
    on stores.warehouse_id = warehouses.warehouse_id