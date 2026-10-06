"""
Conexão com o Postgres e queries cacheadas para o dashboard.
Lê os marts do dbt (schema dbt_dev_marts).
"""
import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("POSTGRES_USER", "supply_admin")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "supply_dev_password")
DB_NAME = os.getenv("POSTGRES_DB", "supply_chain")
DB_HOST = os.getenv("SUPPLY_CHAIN_DB_HOST", "localhost")
DB_PORT = "5432"

SCHEMA = "dbt_dev_marts"


@st.cache_resource
def get_engine():
    url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(url)


@st.cache_data(ttl=600)
def run_query(sql: str) -> pd.DataFrame:
    engine = get_engine()
    return pd.read_sql(sql, engine)


def load_table(table_name: str) -> pd.DataFrame:
    return run_query(f'SELECT * FROM {SCHEMA}."{table_name}"')