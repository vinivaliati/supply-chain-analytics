# Data Dictionary

*[Ver em português mais abaixo / See Portuguese version below](#dicionário-de-dados-português)*

## Raw layer (`raw` schema)

### `suppliers`
| Column | Type | Description |
|---|---|---|
| supplier_id | integer, PK | |
| supplier_name | text | |
| region | text | |
| reliability_score | numeric | Probability of on-time, in-full delivery |
| promised_lead_time_days | integer | Contractual lead time |

### `products`
| Column | Type | Description |
|---|---|---|
| sku_id | integer, PK | |
| sku_name | text | |
| category | text | |
| supplier_id | integer, FK → suppliers | Primary supplier |
| unit_cost | numeric | |
| weight_kg | numeric | |
| abc_curve | text | A / B / C, fixed, drives physical count frequency |

### `warehouses`
| Column | Type | Description |
|---|---|---|
| warehouse_id | integer, PK | |
| warehouse_name | text | |
| region | text | |
| capacity_units | integer | |

### `stores`
| Column | Type | Description |
|---|---|---|
| store_id | integer, PK | |
| store_name | text | |
| region | text | |
| warehouse_id | integer, FK → warehouses | Supplying warehouse |

### `carriers`
| Column | Type | Description |
|---|---|---|
| carrier_id | integer, PK | |
| carrier_name | text | |
| on_time_reliability | numeric | |

### `purchase_orders`
| Column | Type | Description |
|---|---|---|
| po_id | integer, PK | |
| supplier_id | integer, FK | |
| sku_id | integer, FK | |
| warehouse_id | integer, FK | |
| order_date | date | |
| promised_date | date | |
| received_date | date | |
| ordered_qty | integer | |
| received_qty | integer | Can be < ordered_qty (in-full failure) |

### `sales_orders`
| Column | Type | Description |
|---|---|---|
| order_id | integer, PK | |
| sku_id | integer, FK | |
| store_id | integer, FK | |
| warehouse_id | integer, FK | |
| order_date | date | |
| requested_qty | integer | |
| fulfilled_qty | integer | Resolved by the inventory engine; can be < requested |
| promised_delivery_date | date | |
| actual_delivery_date | date | |

### `shipments`
| Column | Type | Description |
|---|---|---|
| shipment_id | integer, PK | |
| order_id | integer, FK → sales_orders | |
| carrier_id | integer, FK | |
| warehouse_id | integer, FK | |
| store_id | integer, FK | |
| ship_date | date | |
| promised_delivery_date | date | |
| actual_delivery_date | date | Source of truth for OTD, not sales_orders.actual_delivery_date |
| distance_km | numeric | |

### `inventory_snapshots`
Grain: one row per `snapshot_date` + `sku_id` + `warehouse_id`.

| Column | Type | Description |
|---|---|---|
| snapshot_date | date | |
| sku_id | integer, FK | |
| warehouse_id | integer, FK | |
| theoretical_stock | integer | Always calculated |
| physical_stock | integer, nullable | Only populated on count days |
| safety_stock | integer | |
| reorder_point | integer | |
| in_transit_qty | integer | Purchased, not yet received |
| avg_daily_demand | numeric | |
| curve | text | Denormalized from products for convenience |
| is_counted | boolean | Whether a physical count happened this day |

### `physical_counts`
Grain: one row per physical count event.

| Column | Type | Description |
|---|---|---|
| count_id | integer, PK | |
| count_date | date | |
| sku_id | integer, FK | |
| warehouse_id | integer, FK | |
| counted_qty | integer | |
| theoretical_qty_at_count | integer | |
| count_type | text | daily / weekly / monthly |

## dbt layers

### Staging (`dbt_dev_staging`)
One `stg_*` model per raw table: typed, deduplicated, renamed. Views.

### Intermediate (`dbt_dev_intermediate`)
| Model | Purpose |
|---|---|
| `int_inventory_physical_projection` | Physical stock projected forward on non-count days |
| `int_order_fulfillment` | Order-level base for OTIF (is_in_full, is_on_time, is_otif) |
| `int_inventory_coverage` | Days of coverage, safety stock / reorder point risk flags |
| `int_stockout_events` | Isolated stockout events with inventory context at order time |

### Marts (`dbt_dev_marts`)
Dimensions: `dim_products`, `dim_suppliers`, `dim_warehouses`, `dim_stores`, `dim_date`.
Facts: `fct_otif`, `fct_inventory_daily`, `fct_stockouts` (with `estimated_lost_revenue`), `fct_transit_performance`.

### Snapshots (`snapshots`)
`products_abc_curve_snapshot` — SCD Type 2 history of each SKU's ABC curve.

---

## Dicionário de dados (português)

## Camada raw (schema `raw`)

### `suppliers`
| Coluna | Tipo | Descrição |
|---|---|---|
| supplier_id | integer, PK | |
| supplier_name | text | |
| region | text | |
| reliability_score | numeric | Probabilidade de entrega no prazo e completa |
| promised_lead_time_days | integer | Lead time contratual |

### `products`
| Coluna | Tipo | Descrição |
|---|---|---|
| sku_id | integer, PK | |
| sku_name | text | |
| category | text | |
| supplier_id | integer, FK → suppliers | Fornecedor principal |
| unit_cost | numeric | |
| weight_kg | numeric | |
| abc_curve | text | A / B / C, fixo, define frequência de contagem física |

### `warehouses`
| Coluna | Tipo | Descrição |
|---|---|---|
| warehouse_id | integer, PK | |
| warehouse_name | text | |
| region | text | |
| capacity_units | integer | |

### `stores`
| Coluna | Tipo | Descrição |
|---|---|---|
| store_id | integer, PK | |
| store_name | text | |
| region | text | |
| warehouse_id | integer, FK → warehouses | CD abastecedor |

### `carriers`
| Coluna | Tipo | Descrição |
|---|---|---|
| carrier_id | integer, PK | |
| carrier_name | text | |
| on_time_reliability | numeric | |

### `purchase_orders`
| Coluna | Tipo | Descrição |
|---|---|---|
| po_id | integer, PK | |
| supplier_id | integer, FK | |
| sku_id | integer, FK | |
| warehouse_id | integer, FK | |
| order_date | date | |
| promised_date | date | |
| received_date | date | |
| ordered_qty | integer | |
| received_qty | integer | Pode ser < ordered_qty (falha de in-full) |

### `sales_orders`
| Coluna | Tipo | Descrição |
|---|---|---|
| order_id | integer, PK | |
| sku_id | integer, FK | |
| store_id | integer, FK | |
| warehouse_id | integer, FK | |
| order_date | date | |
| requested_qty | integer | |
| fulfilled_qty | integer | Resolvido pelo motor de estoque; pode ser < requested |
| promised_delivery_date | date | |
| actual_delivery_date | date | |

### `shipments`
| Coluna | Tipo | Descrição |
|---|---|---|
| shipment_id | integer, PK | |
| order_id | integer, FK → sales_orders | |
| carrier_id | integer, FK | |
| warehouse_id | integer, FK | |
| store_id | integer, FK | |
| ship_date | date | |
| promised_delivery_date | date | |
| actual_delivery_date | date | Fonte de verdade para OTD, não sales_orders.actual_delivery_date |
| distance_km | numeric | |

### `inventory_snapshots`
Grão: uma linha por `snapshot_date` + `sku_id` + `warehouse_id`.

| Coluna | Tipo | Descrição |
|---|---|---|
| snapshot_date | date | |
| sku_id | integer, FK | |
| warehouse_id | integer, FK | |
| theoretical_stock | integer | Sempre calculado |
| physical_stock | integer, nullable | Preenchido só nos dias de contagem |
| safety_stock | integer | |
| reorder_point | integer | |
| in_transit_qty | integer | Comprado, ainda não recebido |
| avg_daily_demand | numeric | |
| curve | text | Desnormalizado de products por conveniência |
| is_counted | boolean | Se houve contagem física nesse dia |

### `physical_counts`
Grão: uma linha por evento de contagem física.

| Coluna | Tipo | Descrição |
|---|---|---|
| count_id | integer, PK | |
| count_date | date | |
| sku_id | integer, FK | |
| warehouse_id | integer, FK | |
| counted_qty | integer | |
| theoretical_qty_at_count | integer | |
| count_type | text | daily / weekly / monthly |

## Camadas do dbt

### Staging (`dbt_dev_staging`)
Um model `stg_*` por tabela raw: tipado, deduplicado, renomeado. Views.

### Intermediate (`dbt_dev_intermediate`)
| Model | Propósito |
|---|---|
| `int_inventory_physical_projection` | Estoque físico projetado nos dias sem contagem |
| `int_order_fulfillment` | Base de pedidos para o OTIF (is_in_full, is_on_time, is_otif) |
| `int_inventory_coverage` | Dias de cobertura, flags de risco de estoque de segurança/ponto de pedido |
| `int_stockout_events` | Eventos de ruptura isolados, com contexto de estoque no momento do pedido |

### Marts (`dbt_dev_marts`)
Dimensões: `dim_products`, `dim_suppliers`, `dim_warehouses`, `dim_stores`, `dim_date`.
Fatos: `fct_otif`, `fct_inventory_daily`, `fct_stockouts` (com `estimated_lost_revenue`), `fct_transit_performance`.

### Snapshots (`snapshots`)
`products_abc_curve_snapshot` — histórico SCD Tipo 2 da curva ABC de cada SKU.