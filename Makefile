-include .env
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

# dbt build roda snapshot, modelos e testes na ordem do grafo.
# Apaga target/ antes: o dbt do Airflow (outra versao) grava ali num formato incompativel.
dbt-build:
	cd $(DBT_DIR) && rm -rf target && $(DBT) deps && $(DBT) build

test:
	cd $(DBT_DIR) && $(DBT) test
