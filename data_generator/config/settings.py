"""
Configurações centrais do gerador de dados de supply chain.
Ajuste estes parâmetros para controlar o volume e o período dos dados simulados.
"""
from datetime import date

RANDOM_SEED = 42

# Período de simulação
START_DATE = date(2026, 1, 1)
END_DATE = date(2026, 12, 31)

# Volumetria das dimensões
N_SUPPLIERS = 15
N_PRODUCTS = 120
N_WAREHOUSES = 4
N_STORES = 25
N_CARRIERS = 6

# Distribuição da curva ABC (deve somar 1.0)
ABC_CURVE_DISTRIBUTION = {
    "A": 0.20,  # contagem diária
    "B": 0.30,  # contagem semanal
    "C": 0.50,  # contagem mensal
}

# Regiões usadas para localizar fornecedores, CDs e lojas
REGIONS = [
    "Sudeste",
    "Sul",
    "Nordeste",
    "Centro-Oeste",
    "Norte",
]

# Categorias de produto
PRODUCT_CATEGORIES = [
    "Eletrônicos",
    "Alimentos",
    "Higiene e Limpeza",
    "Vestuário",
    "Papelaria",
    "Ferramentas",
]

OUTPUT_DIR = "data_generator/output"