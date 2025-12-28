import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
import utils

def show():
    st.header("🥗 Nutrition & Macros")

    # 1. CHARGEMENT DES DONNÉES
    df_food_db = utils.load_data(utils.FOOD_DB_FILE, ["Aliment", "Kcal", "Proteines", "Glucides", "Lipides"])
    df_log = utils.load_data(utils.NUTRITION_LOG_FILE, ["Date", "Aliment", "Quantite", "Kcal_Total", "Prot_Total", "Glu_Total", "Lip_Total"])

    # --- SECTION A: AJOUTER UN ALIMENT A LA BASE ---
    with st.expander("➕ Créer un nouvel aliment"):
        c1, c2, c3, c4, c5 = st.columns(5)
        new_name = c1.text_input("Nom")
        new_kcal = c2.number_input("Kcal", step=1)
        new_prot = c3.number_input("Prot (g)", step=0.1)
        new_carb = c4.number_input("Glu (g)", step=0.1)
        new_fat = c5.number_input("Lip (g)", step=0.1)
        
        if st.button("Ajouter à la base"):
            if new_name and new_name not in df_food_db['Aliment'].values:
                new_row = pd.DataFrame({
                    "Aliment": [new_name], "Kcal": [new_kcal], 
                    "Proteines": [new_prot], "Glucides": [new_carb], "Lipides": [new_fat]
                })
                df_food_db = pd.concat([df_food_db, new_row], ignore_index=True)
                utils.save_data(df_food_db, utils.FOOD_DB_FILE)
                st.success(f"{new_name} ajouté !")
                st.rerun()
            elif new_name in df_food_db['Aliment'].values:
                st.error("Cet aliment existe déjà.")

    st.markdown("---")

    # --- SECTION B: JOURNAL DE LA JOURNÉE ---
    col_date, col_summary = st.columns([1, 2])
    with col_date:
        selected_date = st.date_input("Date du repas", datetime.today(), key="n_date")
        selected_ts = pd.to_datetime(selected_date)
    
    # Filtrer le journal pour la date sélectionnée
    daily_log = df_log[df_log['Date'] == selected_ts]

    # Calcul des totaux
    total_kcal = daily_log['Kcal_Total'].sum()
    total_prot = daily_log['Prot_Total'].sum()
    total_carb = daily_log['Glu_Total'].sum()
    total_fat = daily_log['Lip_Total'].sum()

    with col_summary:
        st.markdown("### Bilan Journalier")
        c_k, c_p, c_g, c_l = st.columns(4)
        c_k.metric("Kcal", int(total_kcal))
        c_p.metric("Prot", f"{total_prot:.1f}g")
        c_g.metric("Glu", f"{total_carb:.1f}g")
        c_l.metric("Lip", f"{total_fat:.1f}g")

    st.markdown("---")

    # --- SECTION C: AJOUTER UNE CONSOMMATION ---
    st.subheader("🍽️ Ajouter un repas")
    
    if df_food_db.empty:
        st.warning("Commencez par ajouter des aliments dans la base ci-dessus.")
    else:
        c_food, c_qty, c_add = st.columns([2, 1, 1])
        with c_food:
            food_choice = st.selectbox("Choisir l'aliment", df_food_db['Aliment'].unique())
        with c_qty:
            qty = st.number_input("Nombre de portions", value=1.0, step=0.5)
        with c_add:
            st.write("")
            st.write("")
            if st.button("Manger", use_container_width=True):
                # Récupérer les infos de l'aliment
                food_info = df_food_db[df_food_db['Aliment'] == food_choice].iloc[0]
                
                new_log_entry = pd.DataFrame({
                    "Date": [selected_ts],
                    "Aliment": [food_choice],
                    "Quantite": [qty],
                    "Kcal_Total": [food_info['Kcal'] * qty],
                    "Prot_Total": [food_info['Proteines'] * qty],
                    "Glu_Total": [food_info['Glucides'] * qty],
                    "Lip_Total": [food_info['Lipides'] * qty]
                })
                df_log = pd.concat([df_log, new_log_entry], ignore_index=True)
                utils.save_data(df_log, utils.NUTRITION_LOG_FILE)
                st.success("Miam !")
                st.rerun()

    # --- SECTION D: LISTE DES REPAS ---
    st.markdown("### Détails des repas")
    if not daily_log.empty:
        # On affiche juste les colonnes utiles
        display_df = daily_log[["Aliment", "Quantite", "Kcal_Total", "Prot_Total", "Glu_Total", "Lip_Total"]]
        st.dataframe(display_df, use_container_width=True)
        
        # Bouton suppression simple (supprime le dernier entré ce jour)
        if st.button("Annuler dernier ajout"):
            # Trouver l'index du dernier élément de ce jour
            last_idx = daily_log.index[-1]
            df_log = df_log.drop(last_idx)
            utils.save_data(df_log, utils.NUTRITION_LOG_FILE)
            st.rerun()
    else:
        st.info("Rien mangé pour le moment.")
