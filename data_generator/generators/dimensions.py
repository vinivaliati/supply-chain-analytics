"""
Gera as tabelas de dimensão (dados estáticos, sem histórico temporal):
- suppliers
- products
- warehouses
- stores
- carriers
"""
import numpy as np
import pandas as pd
from faker import Faker

from data_generator.config.settings import (
    N_SUPPLIERS,
    N_PRODUCTS,
    N_WAREHOUSES,
    N_STORES,
    N_CARRIERS,
    ABC_CURVE_DISTRIBUTION,
    REGIONS,
    PRODUCT_CATEGORIES,
)

fake = Faker("pt_BR")


def generate_suppliers(rng: np.random.Generator) -> pd.DataFrame:
    """
    Fornecedores com confiabilidade variável.
    reliability_score: probabilidade de entregar no prazo E na quantidade certa.
    Alguns fornecedores são consistentemente bons, outros consistentemente ruins,
    o que gera correlação real entre fornecedor e falhas de OTIF/ruptura.
    """
    suppliers = []
    for i in range(1, N_SUPPLIERS + 1):
        reliability = np.clip(rng.normal(loc=0.85, scale=0.12), 0.4, 0.99)
        promised_lead_time = int(rng.integers(3, 21))  # dias

        suppliers.append(
            {
                "supplier_id": i,
                "supplier_name": fake.company(),
                "region": rng.choice(REGIONS),
                "reliability_score": round(float(reliability), 3),
                "promised_lead_time_days": promised_lead_time,
            }
        )
    return pd.DataFrame(suppliers)


def generate_products(rng: np.random.Generator, supplier_ids: list[int]) -> pd.DataFrame:
    """
    Produtos com curva ABC fixa (define frequência de contagem física depois).
    Cada produto tem um fornecedor principal.
    """
    curves = rng.choice(
        list(ABC_CURVE_DISTRIBUTION.keys()),
        size=N_PRODUCTS,
        p=list(ABC_CURVE_DISTRIBUTION.values()),
    )

    products = []
    for i in range(1, N_PRODUCTS + 1):
        category = rng.choice(PRODUCT_CATEGORIES)
        unit_cost = round(float(rng.uniform(5, 500)), 2)
        weight_kg = round(float(rng.uniform(0.1, 25)), 2)

        products.append(
            {
                "sku_id": i,
                "sku_name": f"{category[:3].upper()}-{fake.word().capitalize()}-{i:04d}",
                "category": category,
                "supplier_id": int(rng.choice(supplier_ids)),
                "unit_cost": unit_cost,
                "weight_kg": weight_kg,
                "abc_curve": curves[i - 1],
            }
        )
    return pd.DataFrame(products)


def generate_warehouses(rng: np.random.Generator) -> pd.DataFrame:
    warehouses = []
    for i in range(1, N_WAREHOUSES + 1):
        warehouses.append(
            {
                "warehouse_id": i,
                "warehouse_name": f"CD {fake.city()}",
                "region": rng.choice(REGIONS),
                "capacity_units": int(rng.integers(50_000, 200_000)),
            }
        )
    return pd.DataFrame(warehouses)


def generate_stores(rng: np.random.Generator, warehouse_ids: list[int]) -> pd.DataFrame:
    stores = []
    for i in range(1, N_STORES + 1):
        stores.append(
            {
                "store_id": i,
                "store_name": f"Loja {fake.city()}",
                "region": rng.choice(REGIONS),
                "warehouse_id": int(rng.choice(warehouse_ids)),
            }
        )
    return pd.DataFrame(stores)


def generate_carriers(rng: np.random.Generator) -> pd.DataFrame:
    carriers = []
    for i in range(1, N_CARRIERS + 1):
        on_time_reliability = np.clip(rng.normal(loc=0.88, scale=0.1), 0.5, 0.99)
        carriers.append(
            {
                "carrier_id": i,
                "carrier_name": fake.company(),
                "on_time_reliability": round(float(on_time_reliability), 3),
            }
        )
    return pd.DataFrame(carriers)


def generate_all_dimensions(rng: np.random.Generator) -> dict[str, pd.DataFrame]:
    """Gera todas as dimensões e retorna um dicionário {nome_tabela: dataframe}."""
    suppliers = generate_suppliers(rng)
    products = generate_products(rng, supplier_ids=suppliers["supplier_id"].tolist())
    warehouses = generate_warehouses(rng)
    stores = generate_stores(rng, warehouse_ids=warehouses["warehouse_id"].tolist())
    carriers = generate_carriers(rng)

    return {
        "suppliers": suppliers,
        "products": products,
        "warehouses": warehouses,
        "stores": stores,
        "carriers": carriers,
    }