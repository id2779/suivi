import streamlit as st
import pandas as pd
import os
import altair as alt
from datetime import datetime, date, timedelta

# --- CONFIGURATION ---
WEIGHT_FILE = 'data.csv'
HABITS_FILE = 'habits.csv'
PASSWORD = "1234"

# --- CONFIGURATION PAGE & THEME ---
st.set_page_config(page_title="Mon Suivi Luxe", page_icon="💎", layout="centered")

# --- CSS PERSONNALISÉ (MODE ÉMERAUDE & NOIR) ---
st.markdown("""
<style>
    /* 1. FOND NOIR PROFOND */
    .stApp {
        background-color: #050505;
        color: #e0e0e0;
    }
    
    /* 2. TITRES ET TEXTES */
    h1, h2, h3 {
        color: #10B981 !important; /* Vert Émeraude */
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 200;
    }
    p, label, .stMarkdown, .stMetricLabel {
        color: #cfcfcf !important;
    }

    /* 3. INPUTS (CHAMPS DE TEXTE) STYLE VERRE */
    .stTextInput > div > div > input, .stNumberInput > div > div > input, .stDateInput > div > div > input {
        background-color: rgba(20, 20, 20, 0.8);
        color: #10B981;
        border: 1px solid #1f2937;
        border-radius: 8px;
    }
    .stTextInput > div > div > input:focus {
        border-color: #10B981;
        box-shadow: 0 0 10px rgba(16, 185, 129, 0.2);
    }

    /* 4. BOUTONS STYLE NÉON/LUXE */
    div.stButton > button {
        background: linear-gradient(135deg, #064e3b 0%, #047857 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(4, 120, 87, 0.3);
        font-weight: bold;
        font-size: 18px; /* Plus gros pour les +/- */
    }
    div.stButton > button:hover {
        background: linear-gradient(135deg, #065f46 0%, #059669 100%);
        box-shadow: 0 6px 20px rgba(16, 185, 129, 0.6);
        transform: translateY(-2px);
    }

    /* 5. ONGLETS (TABS) STYLE FUTURISTE */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        border: none;
        color: #6b7280;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(16, 185, 129, 0.1) !important;
        border: 1px solid #10B981 !important;
        color: #10B981 !important;
        font-weight: bold;
    }

    /* 6. PROGRESS BAR */
    .stProgress > div > div > div > div {
        background-color: #10B981;
        background-image: linear-gradient(90deg, #10B981, #34D399);
    }
</style>
""", unsafe_allow_html=True)

# --- FONCTIONS UTILITAIRES ---
def load_data(file_path, columns):
    if not os.path.exists(file_path):
        return pd.DataFrame(columns=columns)
    df = pd.read_csv(file_path)
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
    return df

def save_data(df, file_path):
    df.to_csv(file_path, index=False)

# --- CALLBACKS ---
def update_water_callback(amount):
    selected_d = st.session_state.get('h_date', datetime.today())
    selected_ts = pd.to_datetime(selected_d)
    df = load_data(HABITS_FILE, ["Date", "Habit", "Value", "Goal"])
    mask = (df['Date'] == selected_ts) & (df['Habit'] == 'Eau')
    
    if df[mask].empty:
        # Initialisation avec la nouvelle valeur
        new_val = max(0.0, 0.0 + amount)
        new_row = pd.DataFrame({"Date": [selected_ts], "Habit": ["Eau"], "Value": [new_val], "Goal": [2.0]})
        df = pd.concat([df, new_row], ignore_index=True)
    else:
        idx = df[mask].index[0]
        current_val = df.at[idx, 'Value']
        # Ajout et Arrondi pour éviter le 2.699999
        new_val = round(max(0.0, current_val + amount), 2)
        df.at[idx, 'Value'] = new_val
        
    save_data(df, HABITS_FILE)

def update_goal_callback():
    selected_d = st.session_state.get('h_date', datetime.today())
    selected_ts = pd.to_datetime(selected_d)
    new_goal = st.session_state.get('h_goal_input', 2.0)
    
    df = load_data(HABITS_FILE, ["Date", "Habit", "Value", "Goal"])
    mask = (df['Date'] == selected_ts) & (df['Habit'] == 'Eau')
    if df[mask].empty:
        new_row = pd.DataFrame({"Date": [selected_ts], "Habit": ["Eau"], "Value": [0.0], "Goal": [new_goal]})
        df = pd.concat([df, new_row], ignore_index=True)
    else:
        idx = df[mask].index[0]
        df.at[idx, 'Goal'] = round(new_goal, 2) # Arrondi à la sauvegarde
        
    save_data(df, HABITS_FILE)

# --- AUTH ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align: center; color: #10B981;'>IDENTIFICATION</h1>", unsafe_allow_html=True)
    password_input = st.text_input("Code d'accès", type="password")
    if password_input == PASSWORD:
        st.session_state.authenticated = True
        st.rerun()
    elif password_input:
        st.error("Accès refusé")
    st.stop()

st.title("💎 Personal Tracker")

tab_weight, tab_habits = st.tabs(["POIDS", "HABITUDES"])

# --- ONGLET 1 : POIDS ---
with tab_weight:
    df_weight = load_data(WEIGHT_FILE, ["Date", "Poids"])
    if not df_weight.empty: df_weight = df_weight.sort_values(by='Date')

    current_w = df_weight.iloc[-1]['Poids'] if not df_weight.empty else 0
    prev_w = df_weight.iloc[-2]['Poids'] if len(df_weight) > 1 else current_w
    diff = current_w - prev_w
    
    col_metric1, col_metric2 = st.columns(2)
    with col_metric1:
        st.metric("Poids Actuel", f"{current_w:.1f} kg", f"{diff:+.1f} kg")

    st.markdown("---")
    
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
            save_data(df_weight, WEIGHT_FILE)
            st.rerun()

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
        if st.button("Sauvegarder Historique"):
            save_data(edited_w, WEIGHT_FILE)
            st.rerun()

# --- ONGLET 2 : HABITUDES ---
with tab_habits:
    df_habits = load_data(HABITS_FILE, ["Date", "Habit", "Value", "Goal"])
    selected_date_ts = pd.to_datetime(st.date_input("Date", datetime.today(), key="h_date"))
    mask = (df_habits['Date'] == selected_date_ts) & (df_habits['Habit'] == 'Eau')
    
    if df_habits[mask].empty: display_water, display_goal = 0.0, 2.0
    else: display_water, display_goal = df_habits[mask].iloc[0]['Value'], df_habits[mask].iloc[0]['Goal']

    # --- PARTIE CORRIGÉE (AFFICHAGE ET BOUTONS) ---
    col_ring, col_ctrl = st.columns([1, 2])
    
    with col_ring:
         # Arrondi formaté ici : :.1f ou :.2f
         percent = int((display_water/display_goal)*100) if display_goal > 0 else 0
         st.metric(
             "HYDRATATION", 
             f"{percent}%", 
             f"{display_water:.2f}L / {display_goal:.1f}L" # <-- Correction affichage (ex: 1.25L / 2.0L)
         )
    
    with col_ctrl:
        st.write("Ajouter consommation (25cl) :")
        c_minus, c_plus = st.columns(2)
        
        # Boutons simplifiés et agrandis par le CSS
        with c_minus: 
            st.button("➖", on_click=update_water_callback, args=(-0.25,), use_container_width=True)
        with c_plus: 
            st.button("➕", on_click=update_water_callback, args=(0.25,), use_container_width=True)
        
        st.write("Objectif (L) :")
        st.number_input(
            "Objectif", 
            value=float(display_goal), 
            step=0.1, 
            format="%.1f", # <-- Force l'affichage input à 1 décimale
            key="h_goal_input", 
            label_visibility="collapsed", 
            on_change=update_goal_callback
        )

    st.progress(min(display_water / display_goal, 1.0) if display_goal > 0 else 0)

    st.markdown("---")
    st.markdown("### HISTORIQUE SEMAINE")
    
    df_water_hist = df_habits[df_habits['Habit'] == 'Eau'].copy().sort_values(by='Date').tail(7)
    if not df_water_hist.empty:
        bars = alt.Chart(df_water_hist).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
            x=alt.X('Date', axis=alt.Axis(format='%d', title=None, labelColor='#888')),
            y=alt.Y('Value', title=None),
            color=alt.condition(
                alt.datum.Value >= alt.datum.Goal,
                alt.value('#10B981'),
                alt.value('#374151')
            ),
            # Arrondi dans l'infobulle au survol
            tooltip=[
                alt.Tooltip('Date', format='%d/%m'), 
                alt.Tooltip('Value', format='.2f', title='Bu (L)'), 
                alt.Tooltip('Goal', format='.1f', title='Obj (L)')
            ]
        )
        line = alt.Chart(df_water_hist).mark_rule(color='#10B981', strokeDash=[2,2]).encode(y='Goal')
        st.altair_chart((bars + line).properties(height=200, background='transparent'), use_container_width=True)
