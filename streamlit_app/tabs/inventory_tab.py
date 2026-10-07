"""
Aba de Estoque: cobertura em dias, divergência físico vs teórico por curva ABC.
"""
import plotly.express as px
import streamlit as st
from db import load_table


def render():
    st.subheader("Estoque")

    fct_inventory = load_table("fct_inventory_daily")

    avg_coverage = fct_inventory["coverage_days_physical"].mean()
    pct_below_safety = fct_inventory["is_below_safety_stock"].mean() * 100
    pct_stockout_days = fct_inventory["is_stockout"].mean() * 100

    col1, col2, col3 = st.columns(3)
    col1.metric("Cobertura média (dias)", f"{avg_coverage:.1f}")
    col2.metric("Dias abaixo do estoque de segurança", f"{pct_below_safety:.1f}%")
    col3.metric("Dias em ruptura de estoque", f"{pct_stockout_days:.1f}%")

    st.divider()

    st.subheader("Divergência físico vs. teórico por curva ABC")
    fct_inventory["divergence"] = (
        fct_inventory["physical_stock_projected"] - fct_inventory["theoretical_stock"]
    ).abs()

    divergence_by_curve = (
        fct_inventory.groupby("curve")["divergence"]
        .mean()
        .reset_index()
        .sort_values("divergence")
    )
    divergence_by_curve.columns = ["Curva", "Divergência média (unidades)"]

    fig = px.bar(
        divergence_by_curve,
        x="Curva",
        y="Divergência média (unidades)",
        title="Divergência média entre físico projetado e teórico, por curva ABC",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "Quanto menos frequente a contagem física (curva C = mensal), maior a "
        "divergência acumulada entre o que o sistema acha e a realidade física."
    )

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        fig2 = px.histogram(
            fct_inventory,
            x="coverage_days_physical",
            nbins=40,
            title="Distribuição de cobertura de estoque (dias)",
            range_x=[0, 60],
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        risk_by_curve = (
            fct_inventory.groupby("curve")["is_below_reorder_point"]
            .mean()
            .mul(100)
            .reset_index()
        )
        risk_by_curve.columns = ["Curva", "% dias abaixo do ponto de pedido"]
        fig3 = px.bar(
            risk_by_curve,
            x="Curva",
            y="% dias abaixo do ponto de pedido",
            title="Risco de ruptura iminente por curva ABC",
        )
        st.plotly_chart(fig3, use_container_width=True)