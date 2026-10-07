"""
DAG que orquestra o pipeline de dados sinteticos de supply chain:
1. Gera os dados (dimensoes, compras, vendas, estoque, contagens, shipments)
2. Carrega os CSVs gerados no Postgres (schema raw)
3. Instala dependencias do dbt (dbt_utils)
4. Roda o snapshot do dbt (SCD2 da curva ABC, lido por dim_products)
5. Roda as transformacoes do dbt (staging -> intermediate -> marts)
6. Roda os testes do dbt
"""
import os
import sys
from datetime import datetime

from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

from airflow import DAG

# Garante que o modulo data_generator seja encontrado dentro do container
sys.path.insert(0, "/opt/airflow")

# Host do Postgres de dados, visto de dentro do container do Airflow.
# Credenciais (POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB) vem do .env
# da raiz do projeto, carregado via env_file no docker-compose.yml do Airflow.
os.environ["SUPPLY_CHAIN_DB_HOST"] = "host.docker.internal"

DBT_PROJECT_DIR = "/opt/airflow/dbt/supply_chain"


def run_data_generation():
    from data_generator.main import main as generate_main
    generate_main()


def run_data_load():
    from data_generator.load_to_postgres import main as load_main
    load_main()


with DAG(
    dag_id="generate_and_load_supply_chain_data",
    description="Gera dados sinteticos de supply chain, carrega no Postgres e roda as transformacoes dbt",
    start_date=datetime(2024, 1, 1),  # noqa: DTZ001
    schedule=None,
    catchup=False,
    tags=["supply-chain", "data-generation", "dbt"],
) as dag:

    generate_data = PythonOperator(
        task_id="generate_data",
        python_callable=run_data_generation,
    )

    load_data = PythonOperator(
        task_id="load_data_to_postgres",
        python_callable=run_data_load,
    )

    dbt_clean = BashOperator(
        task_id="dbt_clean",
        bash_command=f"cd {DBT_PROJECT_DIR} && rm -rf target",
    )

    dbt_deps = BashOperator(
        task_id="dbt_deps",
        bash_command=f"cd {DBT_PROJECT_DIR} && dbt deps",
    )

    dbt_snapshot = BashOperator(
        task_id="dbt_snapshot",
        bash_command=f"cd {DBT_PROJECT_DIR} && dbt snapshot",
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd {DBT_PROJECT_DIR} && dbt run",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd {DBT_PROJECT_DIR} && dbt test",
    )

    generate_data >> load_data >> dbt_clean >> dbt_deps >> dbt_snapshot >> dbt_run >> dbt_test