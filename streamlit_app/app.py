"""
Dashboard de Supply Chain Analytics.
Consome os marts do dbt (schema dbt_dev_marts) via Postgres.
"""
import streamlit as st
from tabs import inventory_tab, otif_tab, stockouts_tab, transit_tab

st.set_page_config(
    page_title="Supply Chain Analytics",
    layout="wide",
)

st.title("Supply Chain Analytics")
st.caption("OTIF, ruptura, estoque e trânsito — dados sintéticos, pipeline dbt + Airflow")

tab_otif, tab_stockouts, tab_inventory, tab_transit = st.tabs(
    ["OTIF", "Ruptura", "Estoque", "Trânsito"]
)

with tab_otif:
    otif_tab.render()

with tab_stockouts:
    stockouts_tab.render()

with tab_inventory:
    inventory_tab.render()

with tab_transit:
    transit_tab.render()