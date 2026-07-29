"""
Carrega os CSVs gerados em data_generator/output/ para o Postgres.
Cada CSV vira uma tabela homônima no schema 'raw'.

Usa SQLAlchemy apenas para abrir a conexão; a carga em si é feita via
execução de SQL (CREATE TABLE + COPY), evitando incompatibilidades do
pandas.to_sql entre diferentes versões de SQLAlchemy (1.4 vs 2.0).
"""
import os
import glob
import io
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_NAME = os.getenv("POSTGRES_DB")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = "5432"

OUTPUT_DIR = "data_generator/output"
SCHEMA = "raw"


def get_engine():
    url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(url)


def _pandas_dtype_to_pg(dtype) -> str:
    """Mapeia tipos do pandas para tipos do Postgres (versão simples, suficiente aqui)."""
    if pd.api.types.is_integer_dtype(dtype):
        return "BIGINT"
    if pd.api.types.is_float_dtype(dtype):
        return "DOUBLE PRECISION"
    if pd.api.types.is_bool_dtype(dtype):
        return "BOOLEAN"
    if pd.api.types.is_datetime64_any_dtype(dtype):
        return "TIMESTAMP"
    return "TEXT"


def _load_csv_to_table(conn, csv_path: str, table_name: str):
    df = pd.read_csv(csv_path)

    columns_sql = ", ".join(
        f'"{col}" {_pandas_dtype_to_pg(dtype)}' for col, dtype in df.dtypes.items()
    )

    conn.execute(text(f'DROP TABLE IF EXISTS {SCHEMA}."{table_name}"'))
    conn.execute(text(f'CREATE TABLE {SCHEMA}."{table_name}" ({columns_sql})'))

    # Usa COPY (via psycopg2 raw connection) para carga rápida em lote
    raw_conn = conn.connection
    cursor = raw_conn.cursor()

    buffer = io.StringIO()
    df.to_csv(buffer, index=False, header=False)
    buffer.seek(0)

    columns_list = ", ".join(f'"{col}"' for col in df.columns)
    cursor.copy_expert(
        f'COPY {SCHEMA}."{table_name}" ({columns_list}) FROM STDIN WITH CSV',
        buffer,
    )
    cursor.close()

    return len(df)


def main():
    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}"))

    csv_files = glob.glob(os.path.join(OUTPUT_DIR, "*.csv"))

    if not csv_files:
        print("Nenhum CSV encontrado. Rode 'python -m data_generator.main' primeiro.")
        return

    for csv_path in sorted(csv_files):
        table_name = os.path.splitext(os.path.basename(csv_path))[0]
        print(f"Carregando {table_name}...")

        with engine.begin() as conn:
            n_rows = _load_csv_to_table(conn, csv_path, table_name)

        print(f"  {n_rows} linhas -> {SCHEMA}.{table_name}")

    print("Carga concluída.")


if __name__ == "__main__":
    main()