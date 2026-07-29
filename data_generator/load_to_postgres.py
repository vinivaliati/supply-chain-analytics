"""
Carrega os CSVs gerados em data_generator/output/ para o Postgres.
Cada CSV vira uma tabela homônima no schema 'raw'.
"""
import os
import glob
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_NAME = os.getenv("POSTGRES_DB")
DB_HOST = "localhost"
DB_PORT = "5432"

OUTPUT_DIR = "data_generator/output"
SCHEMA = "raw"


def get_engine():
    url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(url)


def main():
    engine = get_engine()

    with engine.connect() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}"))
        conn.commit()

    csv_files = glob.glob(os.path.join(OUTPUT_DIR, "*.csv"))

    if not csv_files:
        print("Nenhum CSV encontrado. Rode 'python -m data_generator.main' primeiro.")
        return

    for csv_path in sorted(csv_files):
        table_name = os.path.splitext(os.path.basename(csv_path))[0]
        print(f"Carregando {table_name}...")

        df = pd.read_csv(csv_path)
        df.to_sql(
            table_name,
            engine,
            schema=SCHEMA,
            if_exists="replace",
            index=False,
        )
        print(f"  {len(df)} linhas -> {SCHEMA}.{table_name}")

    print("Carga concluída.")


if __name__ == "__main__":
    main()