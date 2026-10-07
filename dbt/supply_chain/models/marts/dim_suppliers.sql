select
    supplier_id
    , supplier_name
    , region
    , reliability_score
    , promised_lead_time_days
from {{ ref('stg_suppliers') }}
