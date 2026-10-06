"""
Aba de Trânsito: OTD por transportadora, atraso por distância.
"""
import streamlit as st
import plotly.express as px

from db import load_table


def render():
    st.subheader("Trânsito")

    fct_transit = load_table("fct_transit_performance")

    total_shipments = len(fct_transit)
    pct_on_time = fct_transit["is_on_time"].mean() * 100
    avg_delay = fct_transit.loc[fct_transit["delay_days"] > 0, "delay_days"].mean()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total de envios", f"{total_shipments:,}")
    col2.metric("Entregas no prazo", f"{pct_on_time:.1f}%")
    col3.metric("Atraso médio (quando atrasa)", f"{avg_delay:.1f} dias")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        otd_by_carrier = (
            fct_transit.groupby("carrier_name")["is_on_time"]
            .mean()
            .mul(100)
            .reset_index()
            .sort_values("is_on_time", ascending=True)
        )
        otd_by_carrier.columns = ["Transportadora", "OTD (%)"]
        fig = px.bar(
            otd_by_carrier,
            x="OTD (%)",
            y="Transportadora",
            orientation="h",
            title="Entrega no prazo por transportadora",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.scatter(
            fct_transit,
            x="distance_km",
            y="delay_days",
            color="carrier_name",
            title="Atraso vs. distância da rota",
            labels={"distance_km": "Distância (km)", "delay_days": "Atraso (dias)"},
            opacity=0.5,
        )
        st.plotly_chart(fig2, use_container_width=True)