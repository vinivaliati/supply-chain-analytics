"""
Aba de Ruptura: taxa, receita perdida estimada, breakdown por curva ABC.
"""
import plotly.express as px
import streamlit as st
from db import load_table


def render():
    st.subheader("Ruptura de estoque")

    fct_stockouts = load_table("fct_stockouts")
    fct_otif = load_table("fct_otif")

    total_orders = len(fct_otif)
    total_stockouts = len(fct_stockouts)
    stockout_rate = (total_stockouts / total_orders) * 100
    total_lost_revenue = fct_stockouts["estimated_lost_revenue"].sum()
    total_lost_units = fct_stockouts["lost_units"].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("Taxa de ruptura", f"{stockout_rate:.1f}%")
    col2.metric("Unidades perdidas", f"{total_lost_units:,.0f}")
    col3.metric("Receita perdida estimada", f"R$ {total_lost_revenue:,.2f}")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        by_curve = (
            fct_stockouts.groupby("curve")
            .agg(eventos=("order_id", "count"), unidades_perdidas=("lost_units", "sum"))
            .reset_index()
        )
        fig = px.bar(
            by_curve,
            x="curve",
            y="eventos",
            title="Eventos de ruptura por curva ABC",
            labels={"curve": "Curva", "eventos": "Eventos"},
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.pie(
            fct_stockouts,
            names="is_total_stockout",
            title="Ruptura total vs. parcial",
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    st.subheader("Top 10 SKUs com maior receita perdida")
    top_skus = (
        fct_stockouts.groupby("sku_id")["estimated_lost_revenue"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )
    st.dataframe(top_skus, use_container_width=True)