# Pipeline de Analytics de Supply Chain

*[Read in English](README.md)*

Um projeto de portfólio de engenharia de dados ponta a ponta simulando a cadeia de suprimentos de uma empresa de distribuição: geração de dados sintéticos, orquestração com Airflow, transformação com dbt, tudo rodando em Docker.

O projeto foca em quatro áreas de negócio que qualquer operação de supply chain acompanha de perto: **OTIF** (On Time In Full), **ruptura de estoque**, **acurácia de inventário** e **desempenho de transporte**.

![Diagrama de arquitetura](docs/architecture.svg)

## Por que esse projeto

A maioria dos pipelines de dados de portfólio são construídos em cima de um CSV do Kaggle. Esse gera seus próprios dados do zero, com regras de negócio que criam padrões realistas e analisáveis:

- Fornecedores com scores de confiabilidade variados, que geram atrasos reais e envios incompletos
- Uma política de contagem física baseada em curva ABC (diária / semanal / mensal), espelhando como armazéns reais fazem auditoria de estoque
- Uma divergência entre estoque teórico e físico que cresce quanto menos frequente é a contagem de um SKU
- Transportadoras com desempenhos diferentes, afetando a entrega até as lojas

O objetivo não foi só mover dados de A para B, mas construir um conjunto de dados onde os números contam uma história operacional real e então usar o dbt para revelar essa história com modelos testados e documentados.

## Contexto de negócio

| Tema | O que representa | Métrica-chave |
|---|---|---|
| OTIF | Pedidos entregues no prazo e na quantidade certa | % OTIF, decomposto em on-time e in-full |
| Ruptura | Demanda que não pôde ser atendida pelo estoque | Taxa de ruptura, receita perdida estimada |
| Estoque | Níveis de estoque e acurácia de contagem ao longo do tempo | Cobertura em dias, divergência físico vs. teórico |
| Trânsito | Desempenho de entrega CD → loja | % de entrega no prazo, atraso por transportadora/rota |

## Stack técnica

- **Python** — geração de dados sintéticos (pandas, numpy, Faker)
- **PostgreSQL** — data warehouse
- **dbt** — transformação (staging → intermediate → marts), testes, snapshots, modelos incrementais
- **Apache Airflow** — orquestração, rodando em Docker via CeleryExecutor
- **Docker / Docker Compose** — Postgres e Airflow containerizados, cada um em seu próprio compose file

## Arquitetura

```
Gerador Python → Postgres (raw) → dbt staging → dbt intermediate → dbt marts
                                          ↓
                                   snapshot (SCD2)
```

O Airflow orquestra cada etapa acima numa única DAG: gerar dados → carregar no Postgres → limpar artefatos do dbt → instalar pacotes do dbt → rodar os models → snapshot → testes.

## Decisões técnicas importantes

**Projeção de estoque físico ("islands and gaps").** Nem todo SKU é contado todo dia só os de curva A. Nos dias sem contagem física, o model `int_inventory_physical_projection` propaga a última contagem física conhecida para frente e ajusta pelo movimento do estoque teórico desde essa contagem, usando uma técnica clássica de window functions em SQL (`sum() over ... rows unbounded preceding` para criar grupos de contagem, depois `max() over (partition by ... count_group)` para carregar o último valor conhecido). Essa é a alternativa compatível com Postgres ao `IGNORE NULLS`, que o Postgres não suporta.

**Frequência de auditoria por curva ABC.** Curva A (maior valor) é contada diariamente, curva B semanalmente, curva C mensalmente espelhando políticas reais de contagem cíclica de armazém. O gerador simula uma taxa de perda (shrinkage) que se acumula conforme os dias sem contagem passam, então produtos de curva C mostram divergência físico-vs-teórico significativamente maior que curva A exatamente o tipo de insight que esse projeto busca revelar.

**Snapshot SCD Tipo 2.** A curva ABC é fixa nesse dataset, mas um snapshot do dbt (`products_abc_curve_snapshot`) ainda rastreia ela com `dbt_valid_from` / `dbt_valid_to`, demonstrando a técnica para um valor que mudaria em produção.

**Modelo incremental.** `stg_inventory_snapshots_incremental` só reprocessa linhas mais novas que a última data máxima processada, em vez de reprocessar as 175 mil linhas de histórico toda vez o padrão correto para uma tabela de fatos que cresce diariamente em produção.

**Dois ambientes dbt, um projeto.** O dbt roda localmente (para iteração rápida) e dentro do container worker do Airflow (para execuções orquestradas), em versões diferentes do dbt-core por causa de restrições de dependência do Airflow. Ambos apontam para a mesma instância do Postgres via `host.docker.internal`, com credenciais injetadas via `.env`/`env_file`, nunca hardcoded.

## Estrutura do projeto

```
supply-chain-analytics/
├── data_generator/          # Scripts Python que geram os dados sintéticos
├── dbt/supply_chain/        # Projeto dbt (staging, intermediate, marts, snapshots)
├── airflow/                 # DAGs do Airflow e configuração do Docker Compose
├── docker-compose.yml       # Container do Postgres (data warehouse)
└── docs/                    # Diagrama de arquitetura, dicionário de dados
```

## Como rodar

Pré-requisitos: Docker Desktop, WSL2 (Windows) ou um shell Linux/Mac, Python 3.11+.

```bash
# 1. Gerar os dados sintéticos
python -m venv .venv && source .venv/bin/activate
pip install -r data_generator/requirements.txt
python -m data_generator.main

# 2. Subir o Postgres
docker compose up -d

# 3. Carregar os dados
python -m data_generator.load_to_postgres

# 4. Rodar o dbt
cd dbt/supply_chain
dbt deps && dbt run && dbt snapshot && dbt test

# 5. Ou rodar tudo via Airflow
cd ../../airflow
docker compose up -d
# dispare a DAG "generate_and_load_supply_chain_data" em http://localhost:8080

# 6. Abrir o dashboard
cd ../..
SUPPLY_CHAIN_DB_HOST=localhost streamlit run streamlit_app/app.py
```

Veja [docs/data_dictionary.md](docs/data_dictionary.md) para o schema completo.

## Resultados

No dataset gerado (120 SKUs, 4 CDs, 25 lojas, 365 dias):

- **OTIF: 85.2%** (93.7% in-full, 86.1% on-time)
- **Taxa de ruptura: 6.3%** dos pedidos, distribuída de forma similar entre as curvas ABC
- **Divergência de estoque ~23x maior** entre curva A (contagem diária) e curva C (contagem mensal) — evidência direta de que a frequência de contagem afeta a acurácia de estoque, não a taxa de ruptura
- **Entrega no prazo (trânsito): 90.9%**, variando por confiabilidade da transportadora e distância da rota

### Prints do dashboard

| OTIF | Ruptura |
|---|---|
| ![Aba OTIF](docs/otif.png) | ![Aba de ruptura](docs/ruptura.png) |

| Estoque | Trânsito |
|---|---|
| ![Aba de estoque](docs/estoque.png) | ![Aba de trânsito](docs/transito.png) |

## Desafios ao longo do caminho

Construir isso revelou problemas reais de integração, não só de modelagem:

- Colisão de nomes de rede Docker entre dois serviços Postgres compartilhando a mesma rede
- Incompatibilidades entre SQLAlchemy 1.4 e 2.0 nas dependências fixadas do Airflow vs. libs mais novas
- Divergência de versão do dbt-core entre o ambiente local (1.12) e o ambiente restrito do Airflow (resolvido fixando `dbt-postgres==1.9.1`, que puxou uma versão compatível de dbt-core automaticamente)
- Uma regressão na lib `click` que quebrava a inicialização do worker do Celery, corrigida fixando `click==8.2.1`
- `DROP TABLE` do Postgres falhando por causa de views do dbt em cascata, exigindo `CASCADE`

## Licença

MIT