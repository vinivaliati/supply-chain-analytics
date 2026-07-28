"""
Gera pedidos de venda (demanda de lojas/clientes).
A quantidade solicitada (requested_qty) é gerada aqui.
A quantidade atendida (fulfilled_qty) é determinada depois,
pelo motor de estoque (inventory_snapshots), que sabe o saldo disponível dia a dia.
"""
from datetime import timedelta

import numpy as np
import pandas as pd

from data_generator.config.settings import START_DATE, END_DATE


def generate_sales_orders(
    rng: np.random.Generator,
    products: pd.DataFrame,
    stores: pd.DataFrame,
    avg_orders_per_sku_per_month: int = 8,
) -> pd.DataFrame:
    """
    Gera pedidos de venda ao longo do período de simulação.
    fulfilled_qty e actual_delivery_date ficam como None/NaN por enquanto,
    serão preenchidos pelo motor de estoque.
    """
    total_days = (END_DATE - START_DATE).days
    n_months = total_days / 30

    orders = []
    order_id = 1

    for _, product in products.iterrows():
        sku_id = int(product["sku_id"])

        n_orders = int(avg_orders_per_sku_per_month * n_months)
        order_days = rng.integers(0, total_days, size=n_orders)

        for day_offset in sorted(order_days):
            order_date = START_DATE + timedelta(days=int(day_offset))
            store_id = int(rng.choice(stores["store_id"].values))
            warehouse_id = int(stores.set_index("store_id").loc[store_id, "warehouse_id"])

            requested_qty = int(rng.integers(1, 40))

            # Prazo prometido de entrega ao cliente/loja (SLA interno)
            promised_delivery_date = order_date + timedelta(days=int(rng.integers(2, 7)))

            orders.append(
                {
                    "order_id": order_id,
                    "sku_id": sku_id,
                    "store_id": store_id,
                    "warehouse_id": warehouse_id,
                    "order_date": order_date,
                    "requested_qty": requested_qty,
                    "fulfilled_qty": None,          # preenchido depois
                    "promised_delivery_date": promised_delivery_date,
                    "actual_delivery_date": None,   # preenchido depois
                }
            )
            order_id += 1

    df = pd.DataFrame(orders)
    df = df.sort_values("order_date").reset_index(drop=True)
    return df