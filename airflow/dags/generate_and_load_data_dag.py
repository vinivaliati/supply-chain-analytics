"""
DAG que orquestra o pipeline de dados sinteticos de supply chain:
1. Gera os dados (dimensoes, compras, vendas, estoque, contagens, shipments)
2. Carrega os CSVs gerados no Postgres (schema raw)
"""
import os
import sys
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

# Garante que o modulo data_generator seja encontrado dentro do container
sys.path.insert(0, "/opt/airflow")
os.environ["DB_HOST"] = "host.docker.internal"


def run_data_generation():
    from data_generator.main import main as generate_main
    generate_main()


def run_data_load():
    from data_generator.load_to_postgres import main as load_main
    load_main()


with DAG(
    dag_id="generate_and_load_supply_chain_data",
    description="Gera dados sinteticos de supply chain e carrega no Postgres (schema raw)",
    start_date=datetime(2024, 1, 1),
    schedule=None,  # por enquanto, só roda manualmente
    catchup=False,
    tags=["supply-chain", "data-generation"],
) as dag:

    generate_data = PythonOperator(
        task_id="generate_data",
        python_callable=run_data_generation,
    )

    load_data = PythonOperator(
        task_id="load_data_to_postgres",
        python_callable=run_data_load,
    )

    generate_data >> load_data