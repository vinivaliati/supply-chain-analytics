# CLAUDE.md

## Visão geral

Projeto de portfólio de engenharia de dados que simula a cadeia de suprimentos de uma distribuidora, de ponta a ponta:

```
Gerador Python → Postgres (raw) → dbt staging → dbt intermediate → dbt marts → Streamlit
                                        ↓
                                 snapshot (SCD2)
```

Quatro temas de negócio: **OTIF**, **ruptura de estoque**, **acurácia de inventário** e **desempenho de transporte**. O Airflow orquestra tudo numa única DAG. Documentação, comentários e mensagens de commit são em português.

## Estrutura de pastas

| Caminho | Papel |
|---|---|
| `data_generator/` | Gera os dados sintéticos. `main.py` grava 10 CSVs em `output/`; `load_to_postgres.py` carrega cada CSV como tabela no schema `raw` (DROP ... CASCADE + CREATE + COPY). Parâmetros e seed em `config/settings.py`. |
| `docker-compose.yml` | Postgres 16 do data warehouse (`supply_chain_postgres`, porta 5432). |
| `dbt/supply_chain/` | Projeto dbt: `models/staging`, `models/intermediate`, `models/marts`, `snapshots/`. |
| `dbt/supply_chain/profiles.yml` | Profile único do dbt (local, Airflow e CI). Versionado porque lê tudo de `env_var`; nunca escrever credencial nele. |
| `airflow/` | `Dockerfile`, compose do Airflow 2.9.1 (CeleryExecutor) e a DAG em `dags/generate_and_load_data_dag.py`. |
| `streamlit_app/` | Dashboard. `db.py` conecta no Postgres e lê o schema `dbt_dev_marts`; uma aba por arquivo em `tabs/`. |
| `docs/` | `architecture.svg`, `data_dictionary.md` e prints do dashboard. |
| `warehouse_init/` | Montada em `/docker-entrypoint-initdb.d` do Postgres; hoje vazia. |

## Comandos

Rodar sempre a partir da raiz do repositório, salvo indicação: os caminhos do gerador (`data_generator/output`) são relativos.

```bash
# Ambiente
cp .env.example .env
python -m venv .venv && source .venv/bin/activate
pip install -r data_generator/requirements.txt -r requirements-dev.txt -r streamlit_app/requirements.txt

# Postgres do warehouse
docker compose up -d

# Gerar e carregar dados
python -m data_generator.main
python -m data_generator.load_to_postgres

# dbt: o profile lê POSTGRES_* e SUPPLY_CHAIN_DB_HOST do ambiente.
# O make exporta o .env; para chamar o dbt direto, antes: set -a && . ./.env && set +a
make dbt-build        # dbt deps && dbt build (snapshot, modelos e testes)
make test             # só dbt test
cd dbt/supply_chain
dbt run --select stg_sales_orders+      # um modelo e seus dependentes
dbt run --select stg_inventory_snapshots_incremental --full-refresh

# Airflow (UI em http://localhost:8080, usuário/senha airflow)
cd airflow
docker compose up -d --build
# despausar e disparar a DAG generate_and_load_supply_chain_data

# Lint (o mesmo do CI)
ruff check . && sqlfluff lint dbt/supply_chain/models

# Dashboard
streamlit run streamlit_app/app.py
```

Atalhos do `Makefile` (raiz): `make up` (Postgres + Airflow), `make down` (preserva volumes), `make dbt-build` (`dbt deps && dbt build`), `make test` (`dbt test`).

Ordem da DAG: `generate_data → load_data_to_postgres → dbt_clean → dbt_deps → dbt_build`.

Detalhes que costumam causar erro:

- `dim_products` faz `ref` no snapshot `products_abc_curve_snapshot`, por isso usamos `dbt build`, que resolve a ordem pelo grafo. Com comandos separados, `dbt snapshot` tem de vir antes de `dbt run`.
- O loader recria as tabelas `raw` com `DROP ... CASCADE`, o que derruba as views de staging/intermediate. Depois de recarregar, rode `make dbt-build` de novo.
- Dentro do Airflow o host do warehouse é `host.docker.internal` (fixado na DAG); no `.env` é `localhost`.
- Local (dbt 1.12) e Airflow (dbt 1.9) compartilham `dbt/supply_chain/target/` em formatos incompatíveis: erro `Not a directory` no snapshot se resolve apagando `target/` (o `make dbt-build` e a DAG já fazem isso).
- O CI (`.github/workflows/ci.yml`) roda ruff, sqlfluff e `dbt build` num Postgres vazio a cada PR.
- Mudou `airflow/requirements.txt` ou o `Dockerfile`? Precisa de `docker compose up -d --build`.

## Convenções do dbt

**Camadas** (configuradas em `dbt_project.yml`):

| Camada | Prefixo | Materialização | Schema | Lê de |
|---|---|---|---|---|
| staging | `stg_` | view | `dbt_dev_staging` | apenas `source('raw', ...)` |
| intermediate | `int_` | view | `dbt_dev_intermediate` | `ref` de staging |
| marts | `dim_`, `fct_` | table | `dbt_dev_marts` | `ref` de intermediate, staging ou snapshot |

- Staging é um modelo por tabela raw: CTE `source` → CTE `renamed` com cast explícito de toda coluna (`col::tipo as col`) → dedup por `row_number()` quando há chave → `select` final listando as colunas, sem `select *`.
- Regras de negócio ficam em intermediate. Os `fct_` são finos: selecionam colunas do `int_` correspondente.
- Todo modelo começa com `{{ config(tags=[...]) }}`: `daily` para o que muda a cada carga, `static` para dimensões.
- Estilo SQL: palavras-chave em minúsculas, vírgula no início da linha, CTEs encadeadas com `, nome as (`, colunas qualificadas com o nome da tabela em joins, 4 espaços de indentação.
- Nomes de colunas em inglês e snake_case; chaves `<entidade>_id`; booleanos `is_`/`was_`; quantidades `_qty`; datas `_date`.
- Documentação e testes ficam no YAML da camada (`_staging__sources.yml`, `_staging__models.yml`, `_intermediate__models.yml`, `_marts__models.yml`), com descrições em português. Todo modelo novo entra ali com descrição e, no mínimo, `unique` + `not_null` na chave (ou `dbt_utils.unique_combination_of_columns` para chave composta) e `relationships` nas chaves estrangeiras.
- Testes com argumentos usam a sintaxe com `arguments:` (ver `relationships` em `_marts__models.yml`).
- Único pacote: `dbt_utils` 1.1.1. Não há macros próprias.
- SQL precisa ser compatível com Postgres (sem `IGNORE NULLS`, por exemplo; ver `int_inventory_physical_projection`).
- Ao adicionar ou mudar colunas de marts, atualizar `docs/data_dictionary.md` e conferir se alguma aba do Streamlit usa a coluna.

## O que não alterar nem commitar

Nunca commitar:

- `.env` (já está no `.gitignore`). Só o `.env.example` é versionado, com valores fictícios.
- Um `profiles.yml` com credencial escrita. O único versionado é `dbt/supply_chain/profiles.yml`, que só usa `env_var`.
- Credenciais hardcoded em código, YAML ou compose. Tudo vem de `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` e `SUPPLY_CHAIN_DB_HOST`.
- CSVs de `data_generator/output/`, `dbt/supply_chain/target/`, `dbt_packages/`, `logs/`, `airflow/logs/`, `.venv/`.
- Mudanças só de fim de linha (CRLF/LF). Antes de commitar, confira com `git diff -w --stat`; se sair vazio, não há mudança real.

Não alterar sem pedido explícito:

- Versões fixadas em `airflow/requirements.txt` (`dbt-postgres==1.9.1`, `click==8.2.1`) e a imagem `apache/airflow:2.9.1`: foram fixadas para resolver conflitos de dependência do Airflow.
- `RANDOM_SEED` e os parâmetros de `data_generator/config/settings.py`: mudam todo o dataset e invalidam os números da seção "Resultados" do README e os prints.
- Nomes de schema (`raw`, `dbt_dev`, sufixos das camadas): `streamlit_app/db.py` lê `dbt_dev_marts` por nome fixo.
- O `dag_id` `generate_and_load_supply_chain_data`, citado nos READMEs.
- O cabeçalho de licença Apache e a estrutura base de `airflow/docker-compose.yml` (é o compose oficial do Airflow com poucos ajustes).

Manter em sincronia: `README.md` (inglês) e `README.pt-br.md` (português) devem receber as mesmas alterações.

Commits: prefixo convencional (`feat:`, `fix:`, `docs:`) e mensagem em português.
