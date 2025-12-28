import streamlit as st
import pandas as pd
import os

# --- CONSTANTES ---
WEIGHT_FILE = 'data.csv'
HABITS_FILE = 'habits.csv'
FOOD_DB_FILE = 'food_db.csv'       # Base de données des aliments
NUTRITION_LOG_FILE = 'nutrition_log.csv' # Journal de consommation
PASSWORD = "1234"

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

# --- INJECTION CSS (STYLE LUXE) ---
def inject_custom_css():
    st.markdown("""
    <style>
        /* 1. FOND NOIR PROFOND */
        .stApp { background-color: #050505; color: #e0e0e0; }
        
        /* 2. TITRES ET TEXTES */
        h1, h2, h3 { color: #10B981 !important; font-family: 'Helvetica Neue', sans-serif; font-weight: 200; }
        p, label, .stMarkdown, .stMetricLabel, .stSelectbox label { color: #cfcfcf !important; }

        /* 3. INPUTS & SELECTBOX STYLE VERRE */
        .stTextInput > div > div > input, .stNumberInput > div > div > input, .stDateInput > div > div > input, div[data-baseweb="select"] > div {
            background-color: rgba(20, 20, 20, 0.8);
            color: #10B981;
            border: 1px solid #1f2937;
            border-radius: 8px;
        }
        
        /* 4. BOUTONS STYLE NÉON/LUXE */
        div.stButton > button {
            background: linear-gradient(135deg, #064e3b 0%, #047857 100%);
            color: white; border: none; border-radius: 8px;
            padding: 0.5rem 1rem; transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(4, 120, 87, 0.3);
            font-weight: bold; font-size: 16px;
        }
        div.stButton > button:hover {
            background: linear-gradient(135deg, #065f46 0%, #059669 100%);
            box-shadow: 0 6px 20px rgba(16, 185, 129, 0.6);
            transform: translateY(-2px);
        }

        /* 5. ONGLETS STYLE FUTURISTE */
        .stTabs [data-baseweb="tab-list"] { gap: 20px; background-color: transparent; }
        .stTabs [data-baseweb="tab"] {
            height: 50px; background-color: rgba(255, 255, 255, 0.05);
            border-radius: 10px; border: none; color: #6b7280;
        }
        .stTabs [aria-selected="true"] {
            background-color: rgba(16, 185, 129, 0.1) !important;
            border: 1px solid #10B981 !important;
            color: #10B981 !important; font-weight: bold;
        }

        /* 6. PROGRESS BAR */
        .stProgress > div > div > div > div {
            background-color: #10B981;
            background-image: linear-gradient(90deg, #10B981, #34D399);
        }
    </style>
    """, unsafe_allow_html=True)
