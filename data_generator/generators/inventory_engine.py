"""
Motor de simulação de estoque diário.
Processa, dia a dia, os recebimentos (purchase_orders) e a demanda (sales_orders)
para cada combinação sku_id + warehouse_id, mantendo o saldo teórico e decidindo
a quantidade atendida de cada pedido de venda (ruptura quando saldo insuficiente).

Retorna:
- inventory_snapshots: saldo teórico diário por sku/warehouse (+ campos auxiliares)
- sales_orders_resolved: sales_orders original com fulfilled_qty e actual_delivery_date preenchidos
"""
from datetime import timedelta

import numpy as np
import pandas as pd

from data_generator.config.settings import START_DATE, END_DATE


def _initial_stock_estimate(rng: np.random.Generator) -> int:
    """Estoque inicial arbitrário por sku/warehouse, no primeiro dia da simulação."""
    return int(rng.integers(100, 600))


def run_inventory_engine(
    rng: np.random.Generator,
    products: pd.DataFrame,
    warehouses: pd.DataFrame,
    purchase_orders: pd.DataFrame,
    sales_orders: pd.DataFrame,
    safety_stock_days: int = 5,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    date_range = pd.date_range(START_DATE, END_DATE, freq="D")

    po_by_key = purchase_orders.copy()
    po_by_key["received_date"] = pd.to_datetime(po_by_key["received_date"])

    so_by_key = sales_orders.copy()
    so_by_key["order_date"] = pd.to_datetime(so_by_key["order_date"])

    sku_warehouse_pairs = pd.concat(
        [
            po_by_key[["sku_id", "warehouse_id"]],
            so_by_key[["sku_id", "warehouse_id"]],
        ]
    ).drop_duplicates()

    avg_demand_lookup = (
        so_by_key.groupby(["sku_id", "warehouse_id"])["requested_qty"]
        .mean()
        .to_dict()
    )

    snapshots = []
    fulfilled_updates = {}

    for _, pair in sku_warehouse_pairs.iterrows():
        sku_id = int(pair["sku_id"])
        warehouse_id = int(pair["warehouse_id"])

        pos_key = po_by_key[
            (po_by_key["sku_id"] == sku_id) & (po_by_key["warehouse_id"] == warehouse_id)
        ].sort_values("received_date")

        sos_key = so_by_key[
            (so_by_key["sku_id"] == sku_id) & (so_by_key["warehouse_id"] == warehouse_id)
        ].sort_values("order_date")

        avg_daily_demand = avg_demand_lookup.get((sku_id, warehouse_id), 5) / 30
        avg_daily_demand = max(avg_daily_demand, 0.5)

        safety_stock = int(avg_daily_demand * safety_stock_days)
        reorder_point = int(safety_stock * 1.5)

        stock = _initial_stock_estimate(rng)

        receipts_by_day = pos_key.groupby(pos_key["received_date"].dt.date)["received_qty"].sum()
        orders_by_day = sos_key.groupby(sos_key["order_date"].dt.date)

        for current_date in date_range:
            day = current_date.date()

            received_today = int(receipts_by_day.get(day, 0))
            stock += received_today

            demand_today = 0
            if day in orders_by_day.groups:
                day_orders = orders_by_day.get_group(day)
                for _, order in day_orders.iterrows():
                    requested = int(order["requested_qty"])
                    fulfilled = min(requested, max(stock, 0))
                    stock -= fulfilled
                    demand_today += requested

                    actual_delivery_date = None
                    if fulfilled > 0:
                        actual_delivery_date = current_date + timedelta(days=int(rng.integers(1, 4)))

                    fulfilled_updates[order["order_id"]] = (fulfilled, actual_delivery_date)

            snapshots.append(
                {
                    "snapshot_date": current_date,
                    "sku_id": sku_id,
                    "warehouse_id": warehouse_id,
                    "theoretical_stock": stock,
                    "safety_stock": safety_stock,
                    "reorder_point": reorder_point,
                    "in_transit_qty": 0,
                    "avg_daily_demand": round(avg_daily_demand, 2),
                }
            )

    inventory_snapshots = pd.DataFrame(snapshots)

    sales_orders_resolved = sales_orders.copy()
    sales_orders_resolved["fulfilled_qty"] = sales_orders_resolved["order_id"].map(
        lambda oid: fulfilled_updates.get(oid, (0, None))[0]
    )
    sales_orders_resolved["actual_delivery_date"] = sales_orders_resolved["order_id"].map(
        lambda oid: fulfilled_updates.get(oid, (0, None))[1]
    )

    return inventory_snapshots, sales_orders_resolved


def calculate_in_transit_qty(
    inventory_snapshots: pd.DataFrame,
    purchase_orders: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calcula, de forma vetorizada, a quantidade em trânsito (comprada mas não
    recebida) por sku/warehouse/dia, e atualiza a coluna in_transit_qty
    em inventory_snapshots.

    Abordagem: cada PO gera dois eventos de variação de saldo em trânsito:
    +ordered_qty no order_date, -ordered_qty no received_date.
    O saldo em trânsito em cada dia é o acumulado (cumsum) desses eventos.
    """
    po = purchase_orders.copy()
    po["order_date"] = pd.to_datetime(po["order_date"])
    po["received_date"] = pd.to_datetime(po["received_date"])

    entries = po[["sku_id", "warehouse_id", "order_date", "ordered_qty"]].rename(
        columns={"order_date": "event_date"}
    )
    entries["delta"] = entries["ordered_qty"]

    exits = po[["sku_id", "warehouse_id", "received_date", "ordered_qty"]].rename(
        columns={"received_date": "event_date"}
    )
    exits["delta"] = -exits["ordered_qty"]

    events = pd.concat(
        [entries[["sku_id", "warehouse_id", "event_date", "delta"]],
         exits[["sku_id", "warehouse_id", "event_date", "delta"]]]
    )

    daily_delta = (
        events.groupby(["sku_id", "warehouse_id", "event_date"])["delta"]
        .sum()
        .reset_index()
    )

    snapshots = inventory_snapshots.copy()
    snapshots["snapshot_date"] = pd.to_datetime(snapshots["snapshot_date"])

    updated_groups = []
    for (sku_id, warehouse_id), group in snapshots.groupby(["sku_id", "warehouse_id"], sort=False):
        group = group.sort_values("snapshot_date").copy()

        sku_deltas = daily_delta[
            (daily_delta["sku_id"] == sku_id) & (daily_delta["warehouse_id"] == warehouse_id)
        ].set_index("event_date")["delta"]

        daily_series = sku_deltas.reindex(group["snapshot_date"], fill_value=0)
        in_transit = daily_series.cumsum().clip(lower=0)

        group["in_transit_qty"] = in_transit.values
        updated_groups.append(group)

    result = pd.concat(updated_groups).sort_values(["sku_id", "warehouse_id", "snapshot_date"]).reset_index(drop=True)
    return result