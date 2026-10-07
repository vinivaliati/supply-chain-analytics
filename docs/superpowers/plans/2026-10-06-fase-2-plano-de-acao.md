# Fase 2 do supply-chain-analytics: Plano de Ação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Levar o repositório do pipeline local atual até o marco de candidatura (etapas 2.1, 2.2 e 2.3 prontas), aplicando no caminho os cortes da auditoria ponytail que continuam valendo.

**Architecture:** Primeiro uma linha de base verde e uma rede de segurança (CI mínimo), depois limpeza, depois aprofundamento do dbt, e só então nuvem. Cada etapa entrega algo que funciona sozinho. As etapas 2.3 a 2.7 estão aqui em nível de tarefa; cada uma ganha seu próprio plano detalhado quando chegar a vez, porque dependem de decisões e de versões de ferramentas que só se confirmam na hora.

**Tech Stack:** Python 3.11, dbt-core 1.12 + dbt-postgres 1.11 (local e CI), MetricFlow 0.211 (já instalado na `.venv`), Postgres 16, Airflow 2.9.1, GitHub Actions, GitHub Pages; depois Terraform, GCS, BigQuery, Snowflake, Great Expectations.

**Spec:** Apêndice A deste arquivo (roadmap da Fase 2 colado em 2026-10-06) e Apêndice B (auditoria ponytail).

## Global Constraints

- Mesmo repositório, histórico preservado. Pastas novas ao lado das existentes: `infra/`, `.github/`, `quality/`, `ai/`.
- Nunca commitar `.env`, chaves de service account nem credenciais em código. `profiles.yml` só é versionado se ler tudo de `env_var`.
- `README.md` e `README.pt-br.md` recebem as mesmas mudanças.
- Commits com prefixo convencional (`feat:`, `fix:`, `docs:`, `chore:`), em português, uma branch por tarefa.
- Não mudar `RANDOM_SEED` nem os parâmetros de `data_generator/config/settings.py`.
- Nenhuma dependência nova se a stdlib, o dbt ou algo já instalado resolve.
- Todo recurso de nuvem criado por Terraform e destruível com `terraform destroy`.

## Review Focus

- **Banco zerado:** `dbt build` num Postgres vazio (caso do CI) precisa passar sem passo manual; hoje só passa se o snapshot rodar antes do `run`.
- **Clone novo:** quem clona o repositório precisa conseguir rodar sem criar `profiles.yml` à mão.
- **Datas da simulação:** `dim_date` cobre 2024 e os dados são de 2026; qualquer métrica com dimensão de tempo sai vazia.
- **SQL em três dialetos:** `::`, `to_char`, `extract(dow ...)` e subtração de datas funcionam em Postgres e quebram em BigQuery.
- **Custo esquecido ligado:** recurso de nuvem que cobra parado (VM, Composer) sem alerta de orçamento.

## Ordem e por quê

| # | Etapa | Por que nesta posição |
|---|---|---|
| 0 | Linha de base verde | Nada desta sessão foi executado: o `docker` não está disponível no WSL. Sem isso, todo o resto é às cegas. |
| 1 | CI mínimo (parte da 2.2) | Custa ~40 linhas e passa a validar cada mudança seguinte num banco zerado. |
| 2 | Limpeza da auditoria | Menos código para portar, testar e documentar nas etapas seguintes. |
| 3 | 2.1 dbt aprofundado | Critério: `dbt build` limpo e docs online. |
| 4 | 2.2 completa | Só falta o "dbt build só do que mudou" e o badge; depende do site de docs da 2.1. |
| 5 | 2.3 GCP com Terraform | Fecha o marco de candidatura (junto com a Fase 4, que não está neste plano). |
| 6 | 2.4, 2.5, 2.6 | Independentes entre si; fazer em paralelo com as candidaturas. |
| 7 | 2.7 Streaming | Opcional. Recomendação: não fazer até todo o resto estar pronto. |

---

## Etapa 0: Linha de base verde

### Task 0.1: Rodar o pipeline atual de ponta a ponta

**Files:** nenhum arquivo novo; pode exigir ajuste em `.env`.

- [ ] **Step 1:** No Docker Desktop, abrir Settings → Resources → WSL integration e ativar a distro. Verificar: `docker --version` responde no WSL.
- [ ] **Step 2:** Mesclar a branch pendente.

```bash
git switch main && git merge chore/makefile-ordem-snapshot
```

- [ ] **Step 3:** Garantir que o `.env` tem `SUPPLY_CHAIN_DB_HOST=localhost` (dentro do Airflow a DAG já sobrescreve para `host.docker.internal`).
- [ ] **Step 4:** Rodar tudo num banco zerado.

```bash
docker compose down -v && docker compose up -d
source .venv/bin/activate
python -m data_generator.main
python -m data_generator.load_to_postgres
make dbt-build && make test
```

Esperado: `dbt snapshot`, `dbt run` e `dbt test` terminam sem erro. Anotar qualquer teste que falhe: vira a primeira tarefa da etapa 3.

- [ ] **Step 5:** Abrir o dashboard (`streamlit run streamlit_app/app.py`) e comparar os quatro números da seção "Resultados" do README com o que aparece. Se divergirem (o período em `settings.py` é 2026), atualizar os dois READMEs e os prints em `docs/`.
- [ ] **Step 6:** Commit das correções, se houver.

### Task 0.2: Um único `profiles.yml` versionado e senha fora do código

Resolve o "clone novo não roda" e habilita o CI. O profile do Airflow já lê tudo de `env_var`, então pode ser versionado sem expor nada.

**Files:**
- Create: `dbt/supply_chain/profiles.yml` (mover de `dbt/airflow_profile/profiles.yml`)
- Modify: `.gitignore` (remover a linha `profiles.yml`)
- Modify: `airflow/docker-compose.yml` (remover o volume de `airflow_profile`)
- Modify: `Makefile` (carregar o `.env`)
- Modify: `streamlit_app/db.py:14-16` (remover os valores padrão)
- Delete: `dbt/airflow_profile/`, `~/.dbt/profiles.yml`

- [ ] **Step 1:** Mover o arquivo. O dbt procura `profiles.yml` primeiro na pasta do projeto, então nenhum comando precisa de flag.

```bash
git mv -f dbt/airflow_profile/profiles.yml dbt/supply_chain/profiles.yml 2>/dev/null || mv dbt/airflow_profile/profiles.yml dbt/supply_chain/profiles.yml
rmdir dbt/airflow_profile && mv ~/.dbt/profiles.yml ~/.dbt/profiles.yml.bak
```

- [ ] **Step 2:** Em `.gitignore`, apagar a linha `profiles.yml`. Em `airflow/docker-compose.yml`, apagar a linha `- ${AIRFLOW_PROJ_DIR:-.}/../dbt/airflow_profile/profiles.yml:/home/airflow/.dbt/profiles.yml`.
- [ ] **Step 3:** No topo do `Makefile`, exportar o `.env` para os alvos.

```makefile
include .env
export
```

- [ ] **Step 4:** Em `streamlit_app/db.py`, trocar os três `os.getenv` com valor padrão por leitura obrigatória.

```python
DB_USER = os.environ["POSTGRES_USER"]
DB_PASSWORD = os.environ["POSTGRES_PASSWORD"]
DB_NAME = os.environ["POSTGRES_DB"]
```

- [ ] **Step 5:** Verificar: `make dbt-build` passa; `git grep -n supply_dev_password` não retorna nada; `git status` mostra `dbt/supply_chain/profiles.yml` como arquivo novo e nenhum segredo nele.
- [ ] **Step 6:** Commit: `chore: unifica profiles.yml via env_var e remove senha padrao do dashboard`.

---

## Etapa 1: CI mínimo

### Task 1.1: Workflow com lint e `dbt build` em Postgres zerado

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `requirements-dev.txt`
- Create: `.sqlfluff`

- [ ] **Step 1:** Criar `requirements-dev.txt`.

```
dbt-core==1.12.0
dbt-postgres==1.11.0
sqlfluff
sqlfluff-templater-dbt
ruff
```

- [ ] **Step 2:** Criar `.sqlfluff` com o estilo que os modelos já seguem.

```ini
[sqlfluff]
dialect = postgres
templater = dbt
max_line_length = 140

[sqlfluff:templater:dbt]
project_dir = dbt/supply_chain
profiles_dir = dbt/supply_chain

[sqlfluff:layout:type:comma]
line_position = leading

[sqlfluff:rules:capitalisation.keywords]
capitalisation_policy = lower
```

- [ ] **Step 3:** Rodar localmente `ruff check .` e `sqlfluff lint dbt/supply_chain/models`. Para cada regra que falhar em massa, decidir: `sqlfluff fix` (se o diff for só estilo) ou adicionar a regra em `exclude_rules`. Não reescrever modelos à mão por causa de lint.
- [ ] **Step 4:** Criar `.github/workflows/ci.yml`.

```yaml
name: ci
on:
  pull_request:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: ci
          POSTGRES_PASSWORD: ci
          POSTGRES_DB: supply_chain
        ports: ["5432:5432"]
        options: >-
          --health-cmd "pg_isready -U ci"
          --health-interval 5s
          --health-retries 10
    env:
      POSTGRES_USER: ci
      POSTGRES_PASSWORD: ci
      POSTGRES_DB: supply_chain
      SUPPLY_CHAIN_DB_HOST: localhost
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip
      - run: pip install -r data_generator/requirements.txt -r requirements-dev.txt
      - run: ruff check .
      - run: python -m data_generator.main
      - run: python -m data_generator.load_to_postgres
      - run: dbt deps
        working-directory: dbt/supply_chain
      - run: sqlfluff lint dbt/supply_chain/models
      - run: dbt build
        working-directory: dbt/supply_chain
```

- [ ] **Step 5:** Abrir um PR com essa branch. Esperado: job verde. `dbt build` resolve sozinho a ordem snapshot → modelos, então este job é o teste do item "banco zerado" do Review Focus.
- [ ] **Step 6:** Commit: `ci: lint e dbt build em postgres efemero`.

---

## Etapa 2: Limpeza da auditoria

Destino de cada item do Apêndice B:

| Item | Decisão | Onde |
|---|---|---|
| 7 `dbt build` | Aplicar | Task 2.1 |
| 8, 9, 12, 15, 16 (código morto, defaults, sobras) | Aplicar | Task 2.2 |
| 6 tags sem uso | Aplicar | Task 2.2 |
| 11 `actual_delivery_date` em `sales_orders` | Não fazer: apagar o sorteio dessa data desloca a sequência aleatória do gerador e muda o dataset inteiro | - |
| 1 modelos órfãos | Parcial: apagar `stg_physical_counts` e `stg_inventory_snapshots_incremental`; manter `dim_date` e `stg_purchase_orders` | Task 2.2 e etapa 3 |
| 13 colunas mortas | Parcial: apagar três; `physical_vs_theoretical_divergence` vira a base da métrica de acurácia | Task 3.2 |
| 3 dedup no staging | Aplicar junto com a portabilidade, para tocar cada arquivo uma vez só | Task 3.2 |
| 4 dicionário de dados manual | Aplicar quando o site de docs estiver no ar | Task 3.5 |
| 5 `select *` nos `fct_` | Opcional, depois dos contratos; ganho pequeno | Task 3.3 |
| 2 LocalExecutor | Adiar: vira requisito se a 2.3 usar VM pequena | Etapa 5 |
| 14 psycopg2 direto | Não fazer: a 2.3 substitui o loader | - |
| 10 `st.connection` | Não fazer: ganho de 8 linhas, e o destino do dashboard muda na 2.3 | - |

### Task 2.1: Trocar snapshot/run/test por `dbt build`

**Files:**
- Modify: `airflow/dags/generate_and_load_data_dag.py`
- Modify: `Makefile`, `README.md`, `README.pt-br.md`, `CLAUDE.md`

- [ ] **Step 1:** Na DAG, substituir as tarefas `dbt_snapshot`, `dbt_run` e `dbt_test` por uma.

```python
    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=f"cd {DBT_PROJECT_DIR} && dbt build",
    )

    generate_data >> load_data >> dbt_clean >> dbt_deps >> dbt_build
```

- [ ] **Step 2:** No `Makefile`, `dbt-build` passa a ser `cd $(DBT_DIR) && $(DBT) deps && $(DBT) build`. O alvo `test` continua (`dbt test`), para rodar só os testes.
- [ ] **Step 3:** Nos READMEs e no `CLAUDE.md`, trocar `dbt deps && dbt snapshot && dbt run && dbt test` por `dbt deps && dbt build` e ajustar a frase do fluxo da DAG.
- [ ] **Step 4:** Verificar: `python -m py_compile airflow/dags/generate_and_load_data_dag.py`; `make dbt-build` passa; disparar a DAG no Airflow e ver as cinco tarefas verdes.
- [ ] **Step 5:** Commit: `refactor: usa dbt build na dag, no makefile e no readme`.

### Task 2.2: Apagar o que ninguém usa

**Files:**
- Delete: `dbt/supply_chain/models/staging/stg_physical_counts.sql`, `dbt/supply_chain/models/staging/stg_inventory_snapshots_incremental.sql`, `logs/dbt.log`, `airflow/dags/.gitkeep`, `warehouse_init/`
- Modify: `dbt/supply_chain/models/staging/_staging__models.yml` (remover a entrada de `stg_physical_counts`)
- Modify: todos os `.sql` de `models/` (remover a linha `{{ config(tags=[...]) }}`), `dbt/supply_chain/dbt_project.yml`
- Modify: `data_generator/generators/inventory_engine.py`, `physical_counts.py`, `data_generator/main.py`
- Modify: `streamlit_app/app.py`, `streamlit_app/tabs/__init__.py`
- Modify: `data_generator/requirements.txt`, `airflow/requirements.txt`, `docker-compose.yml`, `.gitignore`

- [ ] **Step 1:** dbt. Apagar os dois modelos e a entrada no YAML. Remover a primeira linha de tags de cada modelo:

```bash
cd dbt/supply_chain && grep -rl "config(tags=" models | xargs sed -i "/^{{ config(tags=\[.*\]) }}\r\?$/d"
```

Em `dbt_project.yml`, apagar as linhas `analysis-paths`, `test-paths`, `seed-paths`, `macro-paths`, as três `+tags:` e o bloco `seeds:` inteiro.

- [ ] **Step 2:** Modelo incremental. O README anuncia um modelo incremental; em vez de manter a cópia sem uso, tornar incremental a maior tabela de verdade. Em `fct_inventory_daily.sql`:

```sql
{{ config(materialized='incremental', unique_key=['snapshot_date', 'sku_id', 'warehouse_id']) }}
select
    ...
from {{ ref('int_inventory_coverage') }}
{% if is_incremental() %}
where snapshot_date > (select max(snapshot_date) from {{ this }})
{% endif %}
```

Sem `incremental_strategy`: o padrão de cada adaptador funciona em Postgres, BigQuery e Snowflake. Atualizar o parágrafo "Modelo incremental" nos dois READMEs com o nome novo.

- [ ] **Step 3:** Antes de tocar no gerador, guardar a saída atual para comparação: `cp -r data_generator/output /tmp/output_antes`. Nenhuma mudança no gerador pode adicionar, remover ou reordenar chamadas ao `rng`: isso desloca a sequência aleatória e muda todos os números.
- [ ] **Step 4:** Gerador. Em `run_inventory_engine`, remover os parâmetros `products` e `warehouses` (e os argumentos na chamada em `main.py`); trocar `stock = _initial_stock_estimate(rng)` por `stock = int(rng.integers(100, 600))` e apagar a função; em `physical_counts.py`, apagar as duas linhas de `last_known_physical`.
- [ ] **Step 5:** Streamlit. Apagar o `sys.path.insert` de `app.py` (e os `import sys, os` que sobrarem) e esvaziar `tabs/__init__.py`.
- [ ] **Step 6:** Sobras. `git rm logs/dbt.log airflow/dags/.gitkeep`; adicionar `logs/` ao `.gitignore`; remover `python-dateutil` dos dois requirements; remover o volume `./warehouse_init:...` do `docker-compose.yml` e a pasta.
- [ ] **Step 7:** Verificar. O gerador usa seed fixa, então os CSVs têm de sair idênticos:

```bash
python -m data_generator.main
for f in /tmp/output_antes/*.csv; do cmp "$f" "data_generator/output/$(basename "$f")"; done
make dbt-build && streamlit run streamlit_app/app.py
```

Esperado: `cmp` sem nenhuma saída, build verde, quatro abas abrindo.

- [ ] **Step 8:** Commit: `chore: remove modelos, colunas e dependencias sem uso`. PR, CI verde.

---

## Etapa 3: 2.1 dbt aprofundado

### Task 3.1: Testes unitários das regras de negócio (antes de refatorar)

A camada intermediate concentra a lógica e quase não tem teste. Estes testes passam no código atual e travam o comportamento antes da reescrita da Task 3.2.

**Files:**
- Create: `dbt/supply_chain/models/intermediate/_intermediate__unit_tests.yml`

- [ ] **Step 1:** Escrever os testes.

```yaml
unit_tests:
  - name: otif_decompoe_in_full_e_on_time
    model: int_order_fulfillment
    given:
      - input: ref('stg_sales_orders')
        rows:
          - {order_id: 1, requested_qty: 10, fulfilled_qty: 10, promised_delivery_date: 2026-01-10}
          - {order_id: 2, requested_qty: 10, fulfilled_qty: 6, promised_delivery_date: 2026-01-10}
          - {order_id: 3, requested_qty: 10, fulfilled_qty: 10, promised_delivery_date: 2026-01-10}
          - {order_id: 4, requested_qty: 10, fulfilled_qty: 0, promised_delivery_date: 2026-01-10}
      - input: ref('stg_shipments')
        rows:
          - {shipment_id: 1, order_id: 1, actual_delivery_date: 2026-01-09}
          - {shipment_id: 2, order_id: 2, actual_delivery_date: 2026-01-09}
          - {shipment_id: 3, order_id: 3, actual_delivery_date: 2026-01-12}
    expect:
      rows:
        - {order_id: 1, is_in_full: true, is_on_time: true, is_otif: true, was_shipped: true}
        - {order_id: 2, is_in_full: false, is_on_time: true, is_otif: false, was_shipped: true}
        - {order_id: 3, is_in_full: true, is_on_time: false, is_otif: false, was_shipped: true}
        - {order_id: 4, is_in_full: false, is_on_time: false, is_otif: false, was_shipped: false}

  - name: projecao_fisica_carrega_ultima_contagem
    model: int_inventory_physical_projection
    given:
      - input: ref('stg_inventory_snapshots')
        rows:
          # sku 1: contado no dia 1, depois segue o delta do teorico
          - {snapshot_date: 2026-01-01, sku_id: 1, warehouse_id: 1, theoretical_stock: 100, physical_stock: 95, is_counted: true}
          - {snapshot_date: 2026-01-02, sku_id: 1, warehouse_id: 1, theoretical_stock: 90, physical_stock: null, is_counted: false}
          - {snapshot_date: 2026-01-03, sku_id: 1, warehouse_id: 1, theoretical_stock: 120, physical_stock: null, is_counted: false}
          # sku 2: nunca contado, usa o teorico
          - {snapshot_date: 2026-01-01, sku_id: 2, warehouse_id: 1, theoretical_stock: 50, physical_stock: null, is_counted: false}
          # sku 3: projecao negativa e truncada em zero
          - {snapshot_date: 2026-01-01, sku_id: 3, warehouse_id: 1, theoretical_stock: 100, physical_stock: 5, is_counted: true}
          - {snapshot_date: 2026-01-02, sku_id: 3, warehouse_id: 1, theoretical_stock: 10, physical_stock: null, is_counted: false}
    expect:
      rows:
        - {snapshot_date: 2026-01-01, sku_id: 1, physical_stock_projected: 95}
        - {snapshot_date: 2026-01-02, sku_id: 1, physical_stock_projected: 85}
        - {snapshot_date: 2026-01-03, sku_id: 1, physical_stock_projected: 115}
        - {snapshot_date: 2026-01-01, sku_id: 2, physical_stock_projected: 50}
        - {snapshot_date: 2026-01-01, sku_id: 3, physical_stock_projected: 5}
        - {snapshot_date: 2026-01-02, sku_id: 3, physical_stock_projected: 0}
```

- [ ] **Step 2:** Rodar: `dbt test --select test_type:unit`. Esperado: 2 PASS. Se o caso 4 do OTIF falhar em `is_on_time` (nulo em vez de `false`), é um achado real: registrar e corrigir no modelo com `coalesce(..., false)`.
- [ ] **Step 3:** Provar que o teste morde: trocar `<=` por `<` em `is_on_time` no modelo, rodar, ver FAIL, desfazer.
- [ ] **Step 4:** Commit: `test: testes unitarios de otif e projecao de estoque fisico`.

### Task 3.2: Staging enxuto e portável, e correções de dialeto

**Files:**
- Modify: os 9 `dbt/supply_chain/models/staging/stg_*.sql`
- Modify: `dim_date.sql`, `fct_transit_performance.sql`, `int_inventory_physical_projection.sql`, `fct_inventory_daily.sql`
- Modify: `streamlit_app/tabs/inventory_tab.py`

- [ ] **Step 1:** Cada modelo de staging vira um `select` só: sem `deduped` (os testes `unique` das fontes já cobrem a chave) e com `cast` portável no lugar de `::`. Exemplo completo para `stg_carriers.sql`:

```sql
select
    cast(carrier_id as {{ dbt.type_int() }}) as carrier_id
    , cast(carrier_name as {{ dbt.type_string() }}) as carrier_name
    , cast(on_time_reliability as {{ dbt.type_numeric() }}) as on_time_reliability
from {{ source('raw', 'carriers') }}
```

Mapa para os demais: `::integer` → `dbt.type_int()`, `::text` → `dbt.type_string()`, `::numeric(...)` → `dbt.type_numeric()`, `::boolean` → `dbt.type_boolean()`, `::date` → `cast(x as date)`.

- [ ] **Step 2:** `dim_date.sql`: corrigir o período e ficar só com colunas portáveis (ninguém consome `month_name`, `day_name`, `day_of_week`, `week_of_year`).

```sql
with date_spine as (
    -- ponytail: periodo fixo, igual a START_DATE/END_DATE de data_generator/config/settings.py
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2026-01-01' as date)",
        end_date="cast('2027-01-01' as date)"
    ) }}
)
select
    cast(date_day as date) as date_day
    , extract(year from date_day) as year
    , extract(quarter from date_day) as quarter
    , extract(month from date_day) as month
from date_spine
```

- [ ] **Step 3:** `fct_transit_performance.sql`: trocar a subtração de datas por `{{ dbt.datediff('shipments.promised_delivery_date', 'shipments.actual_delivery_date', 'day') }} as delay_days`.
- [ ] **Step 4:** `int_inventory_physical_projection.sql`: remover da saída `physical_stock_actual`, `physical_stock_projected_raw` e `projection_went_negative`. Manter `physical_vs_theoretical_divergence`, expor em `int_inventory_coverage` e `fct_inventory_daily`, e em `inventory_tab.py` trocar o cálculo em pandas por `fct_inventory["physical_vs_theoretical_divergence"].abs()`.
- [ ] **Step 5:** Verificar: `dbt build --full-refresh` verde, incluindo os dois testes unitários; contagem de linhas de cada mart igual à de antes (`select count(*)` antes e depois); aba Estoque mostra o mesmo gráfico de divergência.
- [ ] **Step 6:** Commit: `refactor: staging sem dedup e com casts portaveis; corrige periodo da dim_date`.

### Task 3.3: Contratos e testes nos marts

**Files:**
- Modify: `dbt/supply_chain/models/marts/_marts__models.yml`
- Modify: `dbt/supply_chain/dbt_project.yml`

- [ ] **Step 1:** Ligar contrato para a camada inteira em `dbt_project.yml`:

```yaml
    marts:
      +materialized: table
      +schema: marts
      +contract:
        enforced: true
```

- [ ] **Step 2:** Rodar `dbt build --select marts`. Vai falhar listando, para cada modelo, as colunas e tipos que faltam no YAML. Usar essa saída para preencher `data_type` de todas as colunas dos nove marts, com descrição em português. Exemplo:

```yaml
  - name: fct_otif
    description: "Um pedido de venda por linha, com as flags de OTIF."
    columns:
      - name: order_id
        data_type: integer
        description: "Identificador do pedido."
        constraints:
          - type: not_null
        tests:
          - unique
      - name: is_otif
        data_type: boolean
        description: "Entregue no prazo e na quantidade pedida."
        tests:
          - not_null
```

- [ ] **Step 3:** Completar os testes que faltam: `relationships` de toda chave estrangeira dos `fct_` para a `dim_` correspondente; `dbt_utils.unique_combination_of_columns` em `fct_inventory_daily` (`snapshot_date`, `sku_id`, `warehouse_id`); `accepted_values` em `curve` (`A`, `B`, `C`); `dbt_utils.accepted_range` com `min_value: 0` em `lost_units`, `estimated_lost_revenue`, `distance_km`.
- [ ] **Step 4:** Opcional (auditoria, item 5): com o contrato no YAML sendo a lista oficial de colunas, `fct_otif.sql` pode virar `select * from {{ ref('int_order_fulfillment') }}`. Só fazer se o lint aceitar sem exceção nova.
- [ ] **Step 5:** Verificar: `dbt build` verde. Provar que o contrato morde: renomear uma coluna em `fct_otif.sql`, ver o build falhar com erro de contrato, desfazer.
- [ ] **Step 6:** Commit: `feat: contratos de dados e testes de integridade nos marts`.

### Task 3.4: Camada semântica com MetricFlow

Decisão embutida: `stg_purchase_orders` hoje não alimenta nada. Recomendação: criar `fct_supplier_otif` (um modelo), porque os dados de confiabilidade de fornecedor já são gerados e rendem duas métricas. Se preferir não criar, apagar `stg_purchase_orders`.

**Files:**
- Create: `dbt/supply_chain/models/marts/fct_supplier_otif.sql`
- Create: `dbt/supply_chain/models/marts/_semantic_models.yml`
- Modify: `dbt/supply_chain/models/marts/_marts__models.yml` (time spine em `dim_date`, entrada do modelo novo)

- [ ] **Step 1:** `fct_supplier_otif.sql`:

```sql
select
    po_id
    , supplier_id
    , sku_id
    , warehouse_id
    , order_date
    , promised_date
    , received_date
    , ordered_qty
    , received_qty
    , (received_qty >= ordered_qty) as is_in_full
    , (received_date <= promised_date) as is_on_time
    , (received_qty >= ordered_qty and received_date <= promised_date) as is_otif
from {{ ref('stg_purchase_orders') }}
```

- [ ] **Step 2:** Declarar `dim_date` como time spine:

```yaml
  - name: dim_date
    time_spine:
      standard_granularity_column: date_day
    columns:
      - name: date_day
        granularity: day
```

- [ ] **Step 3:** Primeiro modelo semântico e primeira métrica, para validar a sintaxe na versão instalada antes de escrever o resto:

```yaml
semantic_models:
  - name: orders
    model: ref('fct_otif')
    defaults:
      agg_time_dimension: order_date
    entities:
      - name: order
        type: primary
        expr: order_id
      - name: product
        type: foreign
        expr: sku_id
    dimensions:
      - name: order_date
        type: time
        type_params:
          time_granularity: day
    measures:
      - name: orders_total
        agg: count
        expr: order_id
      - name: orders_otif
        agg: sum
        expr: case when is_otif then 1 else 0 end

metrics:
  - name: otif_rate
    label: OTIF
    type: ratio
    type_params:
      numerator: orders_otif
      denominator: orders_total
```

- [ ] **Step 4:** Validar: `dbt parse && mf validate-configs && mf query --metrics otif_rate --group-by metric_time__month`. Esperado: 12 linhas, valores próximos do OTIF do dashboard. Se `dbt parse` reclamar da estrutura, a versão 1.12 pode exigir a sintaxe mais nova da camada semântica: conferir em docs.getdbt.com (Semantic models) e ajustar antes de seguir.
- [ ] **Step 5:** Repetir o padrão até fechar nove métricas, uma por linha desta tabela:

| Métrica | Tipo | Fonte | Numerador / expressão | Denominador |
|---|---|---|---|---|
| `otif_rate` | ratio | `fct_otif` | pedidos com `is_otif` | pedidos |
| `in_full_rate` | ratio | `fct_otif` | pedidos com `is_in_full` | pedidos |
| `on_time_rate` | ratio | `fct_otif` | pedidos com `is_on_time` | pedidos |
| `stockout_rate` | ratio | `fct_otif` | pedidos com `fulfilled_qty < requested_qty` | pedidos |
| `lost_revenue` | simple | `fct_stockouts` | `sum(estimated_lost_revenue)` | - |
| `inventory_divergence_avg` | simple | `fct_inventory_daily` | `avg(abs(physical_vs_theoretical_divergence))` | - |
| `coverage_days_avg` | simple | `fct_inventory_daily` | `avg(coverage_days_physical)` | - |
| `transit_on_time_rate` | ratio | `fct_transit_performance` | envios com `is_on_time` | envios |
| `supplier_otif_rate` | ratio | `fct_supplier_otif` | POs com `is_otif` | POs |

- [ ] **Step 6:** Verificar: `mf query` de cada métrica agrupada por mês retorna valores; os quatro números de "Resultados" do README batem com `otif_rate`, `stockout_rate` e `transit_on_time_rate` sem agrupamento.
- [ ] **Step 7:** Commit: `feat: camada semantica com nove metricas e otif de fornecedor`.

### Task 3.5: Documentação publicada

Pré-requisito: o repositório precisa ser público para usar GitHub Pages no plano gratuito.

**Files:**
- Modify: `.github/workflows/ci.yml`
- Delete: `docs/data_dictionary.md`
- Modify: `README.md`, `README.pt-br.md`

- [ ] **Step 1:** Antes de apagar o dicionário, copiar para os YAMLs do dbt toda descrição de coluna que só existe nele.
- [ ] **Step 2:** No GitHub: Settings → Pages → Source: GitHub Actions.
- [ ] **Step 3:** Acrescentar ao workflow, depois do `dbt build`, só em push na `main`:

```yaml
      - if: github.ref == 'refs/heads/main'
        run: |
          dbt docs generate
          mkdir -p ../../site
          cp target/index.html target/manifest.json target/catalog.json ../../site/
        working-directory: dbt/supply_chain
      - if: github.ref == 'refs/heads/main'
        uses: actions/upload-pages-artifact@v3
        with:
          path: site

  deploy-docs:
    if: github.ref == 'refs/heads/main'
    needs: build
    runs-on: ubuntu-latest
    permissions:
      pages: write
      id-token: write
    environment:
      name: github-pages
    steps:
      - uses: actions/deploy-pages@v4
```

- [ ] **Step 4:** Verificar: `https://vinivaliati.github.io/supply-chain-analytics/` abre o site do dbt com o grafo de linhagem e as descrições.
- [ ] **Step 5:** Apagar `docs/data_dictionary.md` e trocar, nos dois READMEs, o link do dicionário pelo link do site.
- [ ] **Step 6:** Commit: `docs: publica dbt docs no github pages e remove dicionario manual`.

**Pronto da 2.1:** `dbt build` verde no CI e site no ar.

---

## Etapa 4: 2.2 completa

### Task 4.1: Build só do que mudou, bloqueio de PR e badge

**Files:**
- Modify: `.github/workflows/ci.yml`, `README.md`, `README.pt-br.md`

- [ ] **Step 1:** O site de docs já publica o `manifest.json` da `main`; ele serve de estado. Trocar o passo `dbt build` por:

```yaml
      - name: dbt build (so o que mudou em PR)
        working-directory: dbt/supply_chain
        run: |
          if [ "${{ github.event_name }}" = "pull_request" ] && \
             curl -fsS https://vinivaliati.github.io/supply-chain-analytics/manifest.json -o /tmp/state/manifest.json --create-dirs; then
            dbt build --select "+state:modified+" --state /tmp/state
          else
            dbt build
          fi
```

O `+` à esquerda constrói também os pais, porque o banco do CI nasce vazio.

- [ ] **Step 2:** No GitHub: Settings → Branches → regra para `main` exigindo o check `build` e PR antes de merge.
- [ ] **Step 3:** Badge no topo dos dois READMEs: `![ci](https://github.com/vinivaliati/supply-chain-analytics/actions/workflows/ci.yml/badge.svg)`.
- [ ] **Step 4:** Teste de aceitação: abrir um PR que quebra `is_otif` em `int_order_fulfillment.sql`. Esperado: o log mostra só esse modelo e seus dependentes sendo construídos, o teste unitário falha, o merge fica bloqueado. Fechar o PR sem mesclar.
- [ ] **Step 5:** Commit: `ci: build incremental por estado e badge no readme`.

O `terraform plan` entra no workflow na etapa 5.

---

## Etapa 5: 2.3 GCP com Terraform (plano detalhado próprio ao chegar aqui)

Decisões recomendadas, da mais barata de manter para a mais cara:

- **Carga sem código:** subir os CSVs para o GCS com `gcloud storage cp` e declarar as tabelas `raw` como tabelas externas do BigQuery no próprio Terraform (`external_data_configuration` com `autodetect`). Dispensa escrever um loader novo; o staging já faz os casts.
- **Orquestração:** Cloud Composer custa na casa de centenas de dólares por mês ligado. Recomendação: uma VM pequena rodando o `docker compose` do Airflow que já existe, trocando para `LocalExecutor` (auditoria, item 2) para caber em 4 GB. Custa dezenas de dólares por mês ligada e zero depois do `terraform destroy`. Conferir os dois valores na calculadora do GCP e registrar no README, com a justificativa da escolha.
- **Autenticação do CI:** Workload Identity Federation criada pelo Terraform, sem chave JSON em secret.
- **Trava de custo:** `google_billing_budget` com alerta por e-mail no mesmo `terraform apply`.

Tarefas:

1. Criar projeto GCP e, com um comando `gcloud`, o bucket do estado do Terraform (único passo manual; documentar).
2. `infra/`: provider e backend GCS; bucket de dados; datasets `raw`, `dbt_dev_staging`, `dbt_dev_intermediate`, `dbt_dev_marts`, `snapshots`; tabelas externas; service account e IAM; orçamento.
3. Target `bq` em `dbt/supply_chain/profiles.yml` (`dbt-bigquery`); `dbt build --target bq` verde. As diferenças de dialeto já foram resolvidas na Task 3.2; o que sobrar aparece aqui.
4. VM com script de inicialização que clona o repositório e sobe o Airflow; DAG com `--target bq`.
5. CI: `terraform fmt -check`, `terraform validate` e `terraform plan` em PRs que tocam `infra/`.
6. READMEs: seção de custo, como subir, como destruir.

**Pronto:** `terraform destroy && terraform apply` seguido de uma execução da DAG termina com os marts no BigQuery.

Fora do escopo por ora: apontar o Streamlit para o BigQuery e publicá-lo. Vale fazer quando quiser uma demo pública no ar.

**Marco de candidatura:** etapas 0 a 5 concluídas, mais a Fase 4 (que não faz parte deste plano).

---

## Etapa 6: 2.4, 2.5 e 2.6 (um plano detalhado para cada)

### 2.4 Snowflake

- A conta de teste do Snowflake expira em cerca de 30 dias: só abrir quando a etapa 5 estiver pronta, e fazer tudo numa janela curta.
- Carga: script de ~15 linhas com `write_pandas(..., auto_create_table=True, quote_identifiers=False)`; sem `quote_identifiers=False` as colunas ficam em minúsculas entre aspas e os modelos não as encontram.
- Target `snowflake` no mesmo `profiles.yml`; `dbt build --target snowflake`.
- CI: job disparado à mão (`workflow_dispatch`), não a cada PR, para o CI não quebrar quando a conta expirar. Guardar no README o link da execução verde como evidência.

**Pronto:** os mesmos modelos e testes verdes nos targets `bq` e `snowflake`.

### 2.5 Qualidade de dados

- Os testes de fonte do dbt já validam a entrada depois da carga. O Great Expectations entra antes: valida os CSVs gerados, como primeira tarefa da DAG depois de `generate_data`.
- Um script, `quality/validate_raw.py`, com 5 a 8 expectativas por tabela crítica (chaves não nulas e únicas, quantidades ≥ 0, datas no período, `abc_curve` em A/B/C). Fixar a versão do GE no requirements: a API muda bastante entre versões.
- Alerta: `on_failure_callback` na DAG fazendo POST num webhook do Slack com `urllib.request` da stdlib; a URL vem de variável de ambiente.
- `quality/inject_bad_data.py`: corrompe um CSV de propósito (quantidade negativa, chave nula).

**Pronto:** rodar a injeção, disparar a DAG e receber a mensagem no Slack; print no README.

### 2.6 Text-to-SQL com avaliação

- `ai/questions.yaml`: 25 a 30 perguntas de negócio com o SQL de referência. As nove métricas da Task 3.4 dão as primeiras.
- `ai/eval.py`: para cada pergunta, gera o SQL com um modelo Claude via API usando como contexto as descrições do `manifest.json` do dbt, executa o gerado e o de referência, e compara os conjuntos de linhas (acerto de execução). Saída: `ai/report.md` com a taxa de acerto e a lista de erros com o SQL gerado.
- Servidor MCP em `ai/server.py` com duas ferramentas: descrever os marts e executar consulta.
- Segurança, sem atalho: usuário de banco somente leitura restrito ao schema dos marts, `statement_timeout`, e recusa de qualquer comando que não seja `select`.

**Pronto:** `ai/report.md` versionado com a taxa de acerto e os casos de erro.

---

## Etapa 7: 2.7 Streaming (opcional)

Recomendação: não fazer enquanto houver qualquer item acima em aberto. Se fizer, a versão mínima é um script publicador de eventos de embarque e uma assinatura do Pub/Sub que grava direto no BigQuery (recurso nativo, declarado no Terraform), sem Dataflow.

---

## Apêndice A: Spec (roadmap da Fase 2, colado em 2026-10-06)

Evoluir o repositório atual (mantém o histórico) adicionando `infra/`, `.github/`, `quality/` e `ai/` ao lado das pastas existentes.

- **2.1 dbt aprofundado.** Primeiro revisar o que já existe (testes, contratos). Depois: contratos de dados nos marts, testes mais completos, camada semântica (MetricFlow) com 5 a 10 métricas (OTIF, ruptura, acurácia de estoque, trânsito) e documentação publicada num site. Pronto quando: `dbt build` passa limpo e a documentação está online.
- **2.2 CI/CD.** GitHub Actions com lint, `dbt build` só do que mudou e, mais adiante, `terraform plan`. Pronto quando: um PR quebrado é bloqueado pelo CI e o badge aparece no README.
- **2.3 GCP com Terraform.** Migrar para GCS e BigQuery com Terraform e orquestração do Airflow na nuvem. O Cloud Composer cobra enquanto está ativo: documentar o custo e o `terraform destroy`, ou usar uma alternativa mais barata explicando a escolha. Pronto quando: `terraform apply` sobe tudo do zero.
- **2.4 dbt também em Snowflake.** Segundo target no mesmo projeto dbt, usando uma conta de teste. Pronto quando: os mesmos modelos passam nos dois warehouses.
- **2.5 Qualidade de dados.** Great Expectations nos pontos de entrada, com alertas por Slack ou e-mail. Pronto quando: um dado ruim injetado de propósito dispara alerta.
- **2.6 Text-to-SQL com avaliação.** Perguntas de negócio sobre os marts, com o SQL correto de referência e uma métrica de acerto na execução, exposto como servidor MCP. Pronto quando: existir um relatório com a taxa de acerto e os casos em que erra.
- **2.7 Streaming (opcional).** Eventos de embarque simulados via Pub/Sub até o BigQuery. Só se sobrar tempo.

Marco de candidatura: ao concluir 2.1, 2.2 e 2.3 e a Fase 4, o perfil já é competitivo.

## Apêndice B: Auditoria ponytail (2026-10-06)

1. `delete:` modelos sem consumidor: `stg_inventory_snapshots_incremental`, `stg_physical_counts`, `stg_purchase_orders`, `dim_date`.
2. `native:` CeleryExecutor + Redis + worker + triggerer + flower para uma DAG linear → `LocalExecutor`.
3. `yagni:` CTE `deduped` em 10 modelos de staging.
4. `native:` `docs/data_dictionary.md` manual → `dbt docs generate`.
5. `shrink:` `fct_` que só recopiam o `int_`; listas de colunas repetidas.
6. `yagni:` tags `daily`/`static` e de camada, sem nenhum seletor que as use.
7. `native:` snapshot, run e test separados → `dbt build`.
8. `delete:` parâmetros sem uso em `run_inventory_engine`, wrapper `_initial_stock_estimate`, variável `last_known_physical`.
9. `delete:` caminhos padrão e bloco `seeds:` em `dbt_project.yml`.
10. `native:` `get_engine` + `run_query` → `st.connection`.
11. `delete:` `actual_delivery_date` em `sales_orders`.
12. `delete:` `sys.path.insert` em `app.py` e `tabs/__init__.py`.
13. `delete:` colunas de saída sem leitor em `int_inventory_physical_projection`.
14. `native:` SQLAlchemy só para abrir conexão em `load_to_postgres.py` → `psycopg2.connect`.
15. `delete:` `python-dateutil` nos requirements.
16. `delete:` `logs/dbt.log` versionado, `warehouse_init/` vazia, `.gitkeep`, volumes vazios.
