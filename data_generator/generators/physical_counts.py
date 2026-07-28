"""
Gera contagens físicas de estoque, com frequência baseada na curva ABC do produto:
- Curva A: diária
- Curva B: semanal (toda segunda-feira)
- Curva C: mensal (todo dia 1)

O valor contado (counted_qty) diverge do teórico por um "shrinkage" (perda) simulado,
que se acumula mais em produtos contados com menos frequência (B e C),
já que o erro fica mais tempo sem ser corrigido.
"""
import numpy as np
import pandas as pd


def _should_count(curve: str, current_date: pd.Timestamp) -> bool:
    if curve == "A":
        return True
    if curve == "B":
        return current_date.dayofweek == 0  # segunda-feira
    if curve == "C":
        return current_date.day == 1
    return False


def generate_physical_counts(
    rng: np.random.Generator,
    inventory_snapshots: pd.DataFrame,
    products: pd.DataFrame,
    daily_shrinkage_rate: float = 0.003,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Retorna:
    - physical_counts: eventos de contagem (grão: contagem)
    - inventory_snapshots atualizado: com colunas physical_stock, is_counted, curve
    """
    snapshots = inventory_snapshots.copy()
    snapshots["snapshot_date"] = pd.to_datetime(snapshots["snapshot_date"])

    curve_by_sku = products.set_index("sku_id")["abc_curve"].to_dict()
    snapshots["curve"] = snapshots["sku_id"].map(curve_by_sku)

    counts = []
    count_id = 1

    physical_stock_col = []
    is_counted_col = []

    # Processar por sku+warehouse para manter o "último físico conhecido" corretamente
    for (sku_id, warehouse_id), group in snapshots.groupby(["sku_id", "warehouse_id"], sort=False):
        group = group.sort_values("snapshot_date")
        curve = curve_by_sku[sku_id]

        last_known_physical = None
        days_since_count = 0

        for _, row in group.iterrows():
            days_since_count += 1
            theoretical = row["theoretical_stock"]
            counted_today = _should_count(curve, row["snapshot_date"])

            if counted_today:
                # Shrinkage acumulado desde a última contagem: quanto mais tempo sem contar, mais diverge
                shrinkage = theoretical * daily_shrinkage_rate * days_since_count
                noise = rng.normal(loc=0, scale=theoretical * 0.01 + 1)
                counted_qty = max(0, int(theoretical - shrinkage + noise))

                count_type = {"A": "daily", "B": "weekly", "C": "monthly"}[curve]
                counts.append(
                    {
                        "count_id": count_id,
                        "count_date": row["snapshot_date"],
                        "sku_id": sku_id,
                        "warehouse_id": warehouse_id,
                        "counted_qty": counted_qty,
                        "theoretical_qty_at_count": theoretical,
                        "count_type": count_type,
                    }
                )
                count_id += 1

                last_known_physical = counted_qty
                days_since_count = 0
                physical_stock_col.append(counted_qty)
                is_counted_col.append(True)
            else:
                physical_stock_col.append(None)
                is_counted_col.append(False)

    physical_counts = pd.DataFrame(counts)

    # Nota: para manter a ordem correta ao reatribuir as colunas,
    # reordenamos snapshots pela mesma sequência de groupby usada acima.
    snapshots = snapshots.sort_values(["sku_id", "warehouse_id", "snapshot_date"]).reset_index(drop=True)
    snapshots["physical_stock"] = physical_stock_col
    snapshots["is_counted"] = is_counted_col

    return physical_counts, snapshots