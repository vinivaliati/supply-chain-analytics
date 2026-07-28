"""
Gera pedidos de compra (reposição) dos produtos junto aos fornecedores.
Base para o cálculo de OTIF do lado do fornecedor e para entradas de estoque.
"""
from datetime import timedelta

import numpy as np
import pandas as pd

from data_generator.config.settings import START_DATE, END_DATE


def generate_purchase_orders(
    rng: np.random.Generator,
    products: pd.DataFrame,
    suppliers: pd.DataFrame,
    warehouses: pd.DataFrame,
    orders_per_product_per_year: int = 12,
) -> pd.DataFrame:
    """
    Gera pedidos de compra distribuídos ao longo do período de simulação.
    Cada produto recebe, em média, `orders_per_product_per_year` pedidos
    (aproximadamente mensal), distribuídos entre os CDs.
    """
    suppliers_by_id = suppliers.set_index("supplier_id")
    warehouse_ids = warehouses["warehouse_id"].tolist()

    total_days = (END_DATE - START_DATE).days

    pos = []
    po_id = 1

    for _, product in products.iterrows():
        supplier = suppliers_by_id.loc[product["supplier_id"]]
        reliability = supplier["reliability_score"]
        promised_lead_time = int(supplier["promised_lead_time_days"])

        # Datas de pedido espalhadas ao longo do ano (aprox. mensal, com jitter)
        n_orders = orders_per_product_per_year
        base_offsets = np.linspace(0, total_days - promised_lead_time - 5, n_orders)
        jitter = rng.integers(-5, 6, size=n_orders)
        order_offsets = np.clip(base_offsets + jitter, 0, total_days - promised_lead_time - 5)

        for offset in order_offsets:
            order_date = START_DATE + timedelta(days=int(offset))
            promised_date = order_date + timedelta(days=promised_lead_time)

            # Atraso: quanto menor a confiabilidade, maior a chance e o tamanho do atraso
            is_late = rng.random() > reliability
            if is_late:
                delay_days = int(rng.integers(1, 15))
                received_date = promised_date + timedelta(days=delay_days)
            else:
                # Pode chegar até um pouco antes do prometido
                early_days = int(rng.integers(0, 3))
                received_date = promised_date - timedelta(days=early_days)

            ordered_qty = int(rng.integers(50, 500))

            # Falha de "in full": quantidade recebida menor que a pedida
            is_short = rng.random() > reliability
            if is_short:
                shortage_pct = rng.uniform(0.05, 0.3)
                received_qty = int(ordered_qty * (1 - shortage_pct))
            else:
                received_qty = ordered_qty

            pos.append(
                {
                    "po_id": po_id,
                    "supplier_id": int(product["supplier_id"]),
                    "sku_id": int(product["sku_id"]),
                    "warehouse_id": int(rng.choice(warehouse_ids)),
                    "order_date": order_date,
                    "promised_date": promised_date,
                    "received_date": received_date,
                    "ordered_qty": ordered_qty,
                    "received_qty": received_qty,
                }
            )
            po_id += 1

    return pd.DataFrame(pos)