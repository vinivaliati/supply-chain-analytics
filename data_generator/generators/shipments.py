"""
Gera envios (shipments) entre CD e loja, para pedidos de venda que foram
efetivamente atendidos (fulfilled_qty > 0).

O desempenho de entrega depende da transportadora (on_time_reliability)
e da distância simulada da rota (CD -> loja).
"""
from datetime import timedelta

import numpy as np
import pandas as pd


def generate_shipments(
    rng: np.random.Generator,
    sales_orders_resolved: pd.DataFrame,
    carriers: pd.DataFrame,
) -> pd.DataFrame:
    fulfilled_orders = sales_orders_resolved[sales_orders_resolved["fulfilled_qty"] > 0].copy()

    carrier_ids = carriers["carrier_id"].tolist()
    carriers_by_id = carriers.set_index("carrier_id")

    shipments = []
    shipment_id = 1

    for _, order in fulfilled_orders.iterrows():
        carrier_id = int(rng.choice(carrier_ids))
        carrier = carriers_by_id.loc[carrier_id]
        reliability = carrier["on_time_reliability"]

        # Distância simulada da rota (afeta variabilidade do prazo)
        distance_km = float(rng.uniform(20, 800))

        ship_date = pd.to_datetime(order["order_date"]) + timedelta(days=int(rng.integers(0, 2)))

        # Prazo prometido de entrega já existe no pedido (promised_delivery_date)
        promised_delivery_date = pd.to_datetime(order["promised_delivery_date"])

        # Atraso depende da confiabilidade da transportadora e da distância
        is_late = rng.random() > reliability
        distance_factor = distance_km / 400  # rotas mais longas, mais chance de atraso maior

        if is_late:
            delay_days = int(rng.integers(1, 6) * max(distance_factor, 0.5))
            actual_delivery_date = promised_delivery_date + timedelta(days=delay_days)
        else:
            actual_delivery_date = promised_delivery_date - timedelta(days=int(rng.integers(0, 2)))

        shipments.append(
            {
                "shipment_id": shipment_id,
                "order_id": int(order["order_id"]),
                "carrier_id": carrier_id,
                "warehouse_id": int(order["warehouse_id"]),
                "store_id": int(order["store_id"]),
                "ship_date": ship_date,
                "promised_delivery_date": promised_delivery_date,
                "actual_delivery_date": actual_delivery_date,
                "distance_km": round(distance_km, 1),
            }
        )
        shipment_id += 1

    return pd.DataFrame(shipments)