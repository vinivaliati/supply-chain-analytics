{{ config(tags=['daily']) }}

with source as (
    select * from {{ source('raw', 'physical_counts') }}
)
, renamed as (
    select
        count_id::integer as count_id
        , count_date::date as count_date
        , sku_id::integer as sku_id
        , warehouse_id::integer as warehouse_id
        , counted_qty::integer as counted_qty
        , theoretical_qty_at_count::integer as theoretical_qty_at_count
        , count_type::text as count_type
    from source
)
, deduped as (
    select
        *
        , row_number() over (
            partition by count_id
            order by count_id
        ) as row_num
    from renamed
)
select
    count_id
    , count_date
    , sku_id
    , warehouse_id
    , counted_qty
    , theoretical_qty_at_count
    , count_type
from deduped
where row_num = 1