"""
Aba de OTIF: taxa geral, decomposição in-full/on-time, breakdown por fornecedor.
"""
import pandas as pd
import streamlit as st
import plotly.express as px

from db import load_table


def render():
    st.subheader("OTIF — On Time In Full")

    fct_otif = load_table("fct_otif")
    dim_products = load_table("dim_products")
    dim_suppliers = load_table("dim_suppliers")

    total = len(fct_otif)
    pct_in_full = fct_otif["is_in_full"].mean() * 100
    pct_on_time = fct_otif["is_on_time"].mean() * 100
    pct_otif = fct_otif["is_otif"].mean() * 100

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total de pedidos", f"{total:,}")
    col2.metric("In Full", f"{pct_in_full:.1f}%")
    col3.metric("On Time", f"{pct_on_time:.1f}%")
    col4.metric("OTIF", f"{pct_otif:.1f}%")

    st.divider()

    merged = fct_otif.merge(dim_products, on="sku_id", how="left")
    merged = merged.merge(dim_suppliers, on="supplier_id", how="left")

    otif_by_supplier = (
        merged.groupby("supplier_name")["is_otif"]
        .mean()
        .mul(100)
        .reset_index()
        .sort_values("is_otif", ascending=True)
    )
    otif_by_supplier.columns = ["Fornecedor", "OTIF (%)"]

    fig = px.bar(
        otif_by_supplier,
        x="OTIF (%)",
        y="Fornecedor",
        orientation="h",
        title="OTIF por fornecedor",
    )
    st.plotly_chart(fig, use_container_width=True)

    fct_otif["order_date"] = pd.to_datetime(fct_otif["order_date"])
    otif_by_month = (
        fct_otif.set_index("order_date")
        .resample("ME")["is_otif"]
        .mean()
        .mul(100)
        .reset_index()
    )
    otif_by_month.columns = ["Mês", "OTIF (%)"]

    fig2 = px.line(otif_by_month, x="Mês", y="OTIF (%)", title="OTIF ao longo do tempo", markers=True)
    st.plotly_chart(fig2, use_container_width=True)