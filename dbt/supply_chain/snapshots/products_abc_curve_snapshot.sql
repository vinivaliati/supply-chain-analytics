{% snapshot products_abc_curve_snapshot %}

{{
    config(
        target_schema='snapshots',
        unique_key='sku_id',
        strategy='check',
        check_cols=['abc_curve'],
    )
}}

select
    sku_id
    , sku_name
    , abc_curve
    , supplier_id
from {{ source('raw', 'products') }}

{% endsnapshot %}