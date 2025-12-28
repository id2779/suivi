import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
import utils

def show():
    st.header("🥗 Nutrition & Macros")

    # 1. CHARGEMENT DES DONNÉES (Nouvelles colonnes ajoutées)
    # DB: Ajout de 'Poids_Ref' (ex: pour 100g)
    df_food_db = utils.load_data(utils.FOOD_DB_FILE, ["Aliment", "Kcal", "Proteines", "Glucides", "Lipides", "Poids_Ref"])
    # LOG: Ajout de 'Repas' et 'Poids_Conso'
    df_log = utils.load_data(utils.NUTRITION_LOG_FILE, ["Date", "Repas", "Aliment", "Poids_Conso", "Kcal_Total", "Prot_Total", "Glu_Total", "Lip_Total"])

    # --- SECTION A: CRÉATION ALIMENT (EN GRAMMES) ---
    with st.expander("➕ Ajouter un aliment à la base"):
        st.caption("Entrez les valeurs nutritionnelles pour un poids de référence (généralement 100g).")
        c1, c2, c3 = st.columns([2, 1, 1])
        new_name = c1.text_input("Nom de l'aliment")
        ref_weight = c2.number_input("Poids de référence (g)", value=100, step=10)
        new_kcal = c3.number_input("Kcal", step=1)
        
        c4, c5, c6 = st.columns(3)
        new_prot = c4.number_input("Protéines (g)", step=0.1)
        new_carb = c5.number_input("Glucides (g)", step=0.1)
        new_fat = c6.number_input("Lipides (g)", step=0.1)
        
        if st.button("Sauvegarder dans la base"):
            if new_name and new_name not in df_food_db['Aliment'].values:
                new_row = pd.DataFrame({
                    "Aliment": [new_name],
                    "Kcal": [new_kcal], 
                    "Proteines": [new_prot], 
                    "Glucides": [new_carb], 
                    "Lipides": [new_fat],
                    "Poids_Ref": [ref_weight]
                })
                df_food_db = pd.concat([df_food_db, new_row], ignore_index=True)
                utils.save_data(df_food_db, utils.FOOD_DB_FILE)
                st.success(f"{new_name} ajouté !")
                st.rerun()
            elif new_name in df_food_db['Aliment'].values:
                st.error("Cet aliment existe déjà.")

    st.markdown("---")

    # --- SECTION B: BILAN JOURNALIER ---
    col_date, col_summary = st.columns([1, 2])
    with col_date:
        selected_date = st.date_input("Date", datetime.today(), key="n_date")
        selected_ts = pd.to_datetime(selected_date)
    
    # Filtrer le journal pour la date sélectionnée
    daily_log = df_log[df_log['Date'] == selected_ts]

    # Totaux
    total_kcal = daily_log['Kcal_Total'].sum()
    total_prot = daily_log['Prot_Total'].sum()
    total_carb = daily_log['Glu_Total'].sum()
    total_fat = daily_log['Lip_Total'].sum()

    with col_summary:
        st.markdown("### Total Journée")
        c_k, c_p, c_g, c_l = st.columns(4)
        c_k.metric("Kcal", int(total_kcal))
        c_p.metric("Prot", f"{total_prot:.1f}g")
        c_g.metric("Glu", f"{total_carb:.1f}g")
        c_l.metric("Lip", f"{total_fat:.1f}g")

    st.markdown("---")

    # --- SECTION C: AJOUTER UN REPAS ---
    st.subheader("🍽️ Enregistrer un repas")
    
    if df_food_db.empty:
        st.warning("La base d'aliments est vide.")
    else:
        # Ligne 1 : Quoi et Quand ?
        col_meal, col_food = st.columns([1, 2])
        with col_meal:
            meal_type = st.selectbox("Moment", ["Petit-déjeuner", "Déjeuner", "Dîner", "Snack"])
        with col_food:
            food_choice = st.selectbox("Aliment", df_food_db['Aliment'].unique())

        # Ligne 2 : Combien ?
        col_qty, col_btn = st.columns([2, 1])
        with col_qty:
            # Récupérer l'info pour afficher le poids de ref par défaut
            food_ref_info = df_food_db[df_food_db['Aliment'] == food_choice].iloc[0]
            ref_w = food_ref_info.get('Poids_Ref', 100) # Sécurité si ancienne db
            
            consumed_weight = st.number_input(f"Poids consommé (g)", value=float(ref_w), step=10.0)
            
        with col_btn:
            st.write("") # Espace pour aligner le bouton verticalement
            st.write("")
            if st.button("Manger", use_container_width=True):
                # CALCULS PROPORTIONNELS
                ratio = consumed_weight / ref_w
                
                new_log_entry = pd.DataFrame({
                    "Date": [selected_ts],
                    "Repas": [meal_type],
                    "Aliment": [food_choice],
                    "Poids_Conso": [consumed_weight],
                    "Kcal_Total": [food_ref_info['Kcal'] * ratio],
                    "Prot_Total": [food_ref_info['Proteines'] * ratio],
                    "Glu_Total": [food_ref_info['Glucides'] * ratio],
                    "Lip_Total": [food_ref_info['Lipides'] * ratio]
                })
                df_log = pd.concat([df_log, new_log_entry], ignore_index=True)
                utils.save_data(df_log, utils.NUTRITION_LOG_FILE)
                st.success(f"Ajouté au {meal_type} !")
                st.rerun()

    st.markdown("---")

    # --- SECTION D: DÉTAIL PAR REPAS (4 BLOCS) ---
    st.markdown("### Détails du menu")

    meal_order = ["Petit-déjeuner", "Déjeuner", "Dîner", "Snack"]
    
    for meal in meal_order:
        # Filtrer pour ce repas spécifique
        meal_data = daily_log[daily_log['Repas'] == meal]
        
        with st.expander(f"{meal} ({int(meal_data['Kcal_Total'].sum())} Kcal)", expanded=True):
            if not meal_data.empty:
                # Affichage propre
                display_df = meal_data[["Aliment", "Poids_Conso", "Kcal_Total", "Prot_Total", "Glu_Total", "Lip_Total"]].copy()
                
                # Renommer pour l'affichage
                display_df.columns = ["Aliment", "Poids (g)", "Kcal", "Prot", "Glu", "Lip"]
                
                # Formatage des nombres pour faire joli
                st.dataframe(display_df, use_container_width=True)
                
                # Bouton de suppression pour ce repas spécifique
                # On utilise une clé unique basée sur le repas pour le bouton
                if st.button(f"Supprimer dernier ajout ({meal})", key=f"del_{meal}"):
                    # Trouver le dernier index de ce repas
                    last_idx = meal_data.index[-1]
                    df_log = df_log.drop(last_idx)
                    utils.save_data(df_log, utils.NUTRITION_LOG_FILE)
                    st.rerun()
            else:
                st.caption("Aucun aliment enregistré.")
