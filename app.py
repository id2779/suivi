import streamlit as st
import utils
from tabs import weight, habits, nutrition

# --- CONFIGURATION INITIALE ---
st.set_page_config(page_title="Mon Suivi Luxe", page_icon="💎", layout="centered")
utils.inject_custom_css()

# --- AUTHENTIFICATION ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align: center; color: #10B981;'>IDENTIFICATION</h1>", unsafe_allow_html=True)
    password_input = st.text_input("Code d'accès", type="password")
    if password_input == utils.PASSWORD:
        st.session_state.authenticated = True
        st.rerun()
    elif password_input:
        st.error("Accès refusé")
    st.stop()

# --- APPLICATION PRINCIPALE ---
st.title("💎 Personal Tracker")

# Création des onglets
tab_weight, tab_habits, tab_nutrition = st.tabs(["⚖️ POIDS", "💧 EAU", "🥗 ALIM"])

with tab_weight:
    weight.show()

with tab_habits:
    habits.show()

with tab_nutrition:
    nutrition.show()
