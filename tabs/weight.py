import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
import utils # Import du fichier utils.py

def show():
    st.header("Suivi de Poids")
    
    # Chargement
    df_weight = utils.load_data(utils.WEIGHT_FILE, ["Date", "Poids"])
    if not df_weight.empty:
        df_weight = df_weight.sort_values(by='Date')

    # Métriques
    current_w = df_weight.iloc[-1]['Poids'] if not df_weight.empty else 0
    prev_w = df_weight.iloc[-2]['Poids'] if len(df_weight) > 1 else current_w
    diff = current_w - prev_w
    
    col_metric1, _ = st.columns(2)
    with col_metric1:
        st.metric("Poids Actuel", f"{current_w:.1f} kg", f"{diff:+.1f} kg")

    st.markdown("---")
    
    # Saisie
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1: date_input = st.date_input("Date", datetime.today(), key="w_date")
    with c2: weight_input = st.number_input("Nouveau Poids", value=float(current_w), step=0.1, format="%.1f", key="w_input")
    with c3:
        st.write("")
        st.write("")
        if st.button("ENREGISTRER", use_container_width=True):
            new_entry = pd.DataFrame({"Date": [pd.to_datetime(date_input)], "Poids": [weight_input]})
            df_weight = pd.concat([df_weight, new_entry], ignore_index=True)
            df_weight = df_weight.sort_values(by='Date')
            utils.save_data(df_weight, utils.WEIGHT_FILE)
            st.rerun()

    # Graphique
    if not df_weight.empty:
        st.markdown("### ÉVOLUTION")
        filter_option = st.radio("", ["1 Semaine", "1 Mois", "Tout"], horizontal=True, key="w_filter")
        
        df_chart = df_weight.copy()
        today = datetime.now()
        if filter_option == "1 Semaine": start_date = today - timedelta(days=7)
        elif filter_option == "1 Mois": start_date = today - timedelta(days=30)
        else: start_date = df_chart['Date'].min()
        df_chart = df_chart[df_chart['Date'] >= start_date]

        if not df_chart.empty:
            y_min, y_max = current_w - 5, current_w + 5
            chart = alt.Chart(df_chart).mark_area(
                line={'color':'#10B981'},
                color=alt.Gradient(
                    gradient='linear', stops=[alt.GradientStop(color='#10B981', offset=0), alt.GradientStop(color='rgba(16, 185, 129, 0)', offset=1)],
                    x1=1, x2=1, y1=1, y2=0
                )
            ).encode(
                x=alt.X('Date', axis=alt.Axis(format='%d/%m', grid=False, domainColor='#333', tickColor='#333')),
                y=alt.Y('Poids', scale=alt.Scale(domain=[y_min, y_max]), axis=alt.Axis(gridColor='#333', domainColor='#333')),
                tooltip=['Date', 'Poids']
            ).properties(height=350, background='transparent').interactive()
            st.altair_chart(chart, use_container_width=True)

    with st.expander("Historique Détaillé"):
        edited_w = st.data_editor(df_weight, num_rows="dynamic", key="w_editor", use_container_width=True)
        if st.button("Sauvegarder Historique Poids"):
            utils.save_data(edited_w, utils.WEIGHT_FILE)
            st.rerun()
