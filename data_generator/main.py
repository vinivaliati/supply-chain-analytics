"""
Orquestra a geração de todos os dados do projeto e salva os CSVs
em data_generator/output/.
"""
import os
import time
import numpy as np

from data_generator.config.settings import RANDOM_SEED, OUTPUT_DIR
from data_generator.generators.dimensions import generate_all_dimensions
from data_generator.generators.purchase_orders import generate_purchase_orders
from data_generator.generators.sales_orders import generate_sales_orders
from data_generator.generators.inventory_engine import run_inventory_engine, calculate_in_transit_qty
from data_generator.generators.physical_counts import generate_physical_counts
from data_generator.generators.shipments import generate_shipments


def main():
    rng = np.random.default_rng(RANDOM_SEED)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Gerando dimensões...")
    dimensions = generate_all_dimensions(rng)
    for name, df in dimensions.items():
        df.to_csv(os.path.join(OUTPUT_DIR, f"{name}.csv"), index=False)
        print(f"  {name}: {len(df)} linhas")

    print("Gerando purchase_orders...")
    purchase_orders = generate_purchase_orders(
        rng, dimensions["products"], dimensions["suppliers"], dimensions["warehouses"]
    )
    purchase_orders.to_csv(os.path.join(OUTPUT_DIR, "purchase_orders.csv"), index=False)
    print(f"  purchase_orders: {len(purchase_orders)} linhas")

    print("Gerando sales_orders (demanda bruta)...")
    sales_orders = generate_sales_orders(rng, dimensions["products"], dimensions["stores"])
    print(f"  sales_orders: {len(sales_orders)} linhas")

    print("Rodando motor de estoque...")
    start = time.time()
    inventory_snapshots, sales_orders_resolved = run_inventory_engine(
        rng,
        dimensions["products"],
        dimensions["warehouses"],
        purchase_orders,
        sales_orders,
    )
    elapsed = time.time() - start
    print(f"  inventory_snapshots: {len(inventory_snapshots)} linhas ({elapsed:.1f}s)")

    print("Calculando in_transit_qty...")
    start = time.time()
    inventory_snapshots = calculate_in_transit_qty(inventory_snapshots, purchase_orders)
    elapsed = time.time() - start
    print(f"  concluído ({elapsed:.1f}s)")

    print("Gerando physical_counts (por curva ABC)...")
    start = time.time()
    physical_counts, inventory_snapshots = generate_physical_counts(
        rng, inventory_snapshots, dimensions["products"]
    )
    elapsed = time.time() - start
    print(f"  physical_counts: {len(physical_counts)} linhas ({elapsed:.1f}s)")

    print("Gerando shipments...")
    shipments = generate_shipments(rng, sales_orders_resolved, dimensions["carriers"])
    print(f"  shipments: {len(shipments)} linhas")

    inventory_snapshots.to_csv(os.path.join(OUTPUT_DIR, "inventory_snapshots.csv"), index=False)
    sales_orders_resolved.to_csv(os.path.join(OUTPUT_DIR, "sales_orders.csv"), index=False)
    physical_counts.to_csv(os.path.join(OUTPUT_DIR, "physical_counts.csv"), index=False)
    shipments.to_csv(os.path.join(OUTPUT_DIR, "shipments.csv"), index=False)

    print("Concluído.")


if __name__ == "__main__":
    main()