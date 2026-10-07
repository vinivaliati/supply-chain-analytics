include .env
export

DBT_DIR := dbt/supply_chain
# Usa o dbt da .venv se existir; senão, o do PATH
DBT := $(if $(wildcard .venv/bin/dbt),$(abspath .venv/bin/dbt),dbt)

.PHONY: up down dbt-build test

# Sobe o Postgres do warehouse e depois o Airflow
up:
	docker compose up -d
	docker compose -f airflow/docker-compose.yml up -d

# Derruba tudo sem remover os volumes
down:
	docker compose -f airflow/docker-compose.yml down
	docker compose down

# Snapshot antes do run: dim_products le do snapshot, que so depende de raw.products
dbt-build:
	cd $(DBT_DIR) && $(DBT) deps && $(DBT) snapshot && $(DBT) run

test:
	cd $(DBT_DIR) && $(DBT) test
