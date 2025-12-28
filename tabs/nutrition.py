import streamlit as st
import pandas as pd
import utils
from datetime import datetime

def show():
    st.header("🥗 Nutrition & Macros")

    # --- CHARGEMENT ---
    df_food_db = utils.load_data(utils.FOOD_DB_FILE, ["Aliment", "Kcal", "Proteines", "Glucides", "Lipides", "Poids_Ref"])
    df_log = utils.load_data(utils.NUTRITION_LOG_FILE, ["Date", "Repas", "Aliment", "Poids_Conso", "Kcal_Total", "Prot_Total", "Glu_Total", "Lip_Total"])
    
    # Chargement des objectifs (si fichier vide, valeurs par défaut)
    df_goals = utils.load_data(utils.GOALS_FILE, ["Kcal_Goal", "Prot_Goal", "Glu_Goal", "Lip_Goal"])
    if df_goals.empty:
        current_goals = {"Kcal": 2000, "Prot": 150, "Glu": 200, "Lip": 70}
    else:
        # On prend la dernière ligne configurée
        last_g = df_goals.iloc[-1]
        current_goals = {
            "Kcal": last_g['Kcal_Goal'], "Prot": last_g['Prot_Goal'], 
            "Glu": last_g['Glu_Goal'], "Lip": last_g['Lip_Goal']
        }

    # ====================================================
    # 1. CONFIGURATION DES OBJECTIFS (EXPANDER)
    # ====================================================
    with st.expander("🎯 Définir mes objectifs quotidiens"):
        st.caption("Définissez vos cibles. Les barres de progression s'ajusteront automatiquement.")
        
        target_kcal = st.number_input("Objectif Calories (Kcal)", value=int(current_goals["Kcal"]), step=50)
        
        mode = st.radio("Mode de calcul des macros :", ["Grammes (Précis)", "Pourcentages (%)"], horizontal=True)
        
        c_p, c_g, c_l = st.columns(3)
        
        if mode == "Grammes (Précis)":
            # Mode manuel simple
            target_prot = c_p.number_input("Protéines (g)", value=float(current_goals["Prot"]), step=1.0)
            target_glu = c_g.number_input("Glucides (g)", value=float(current_goals["Glu"]), step=1.0)
            target_lip = c_l.number_input("Lipides (g)", value=float(current_goals["Lip"]), step=1.0)
            
            # Petit check de cohérence calorique pour info
            cal_from_macros = (target_prot * 4) + (target_glu * 4) + (target_lip * 9)
            diff = target_kcal - cal_from_macros
            if abs(diff) > 50:
                st.warning(f"Note : Vos macros totalisent {int(cal_from_macros)} kcal (Différence de {int(diff)} kcal avec l'objectif).")

        else:
            # Mode Pourcentage intelligent
            pct_prot = c_p.number_input("% Protéines", value=30, min_value=0, max_value=100, step=5)
            pct_glu = c_g.number_input("% Glucides", value=40, min_value=0, max_value=100, step=5)
            pct_lip = c_l.number_input("% Lipides", value=30, min_value=0, max_value=100, step=5)
            
            total_pct = pct_prot + pct_glu + pct_lip
            if total_pct > 100:
                st.error(f"Total : {total_pct}% ! Le total ne doit pas dépasser 100%.")
                st.stop()
            elif total_pct < 100:
                st.info(f"Total actuel : {total_pct}%. Il reste {100-total_pct}% à attribuer.")

            # Calcul automatique des grammes
            # Prot & Glu = 4 kcal/g, Lip = 9 kcal/g
            target_prot = (target_kcal * (pct_prot/100)) / 4
            target_glu = (target_kcal * (pct_glu/100)) / 4
            target_lip = (target_kcal * (pct_lip/100)) / 9
            
            st.success(f"Calculé : Prot {int(target_prot)}g | Glu {int(target_glu)}g | Lip {int(target_lip)}g")

        if st.button("Sauvegarder les objectifs"):
            new_goals = pd.DataFrame({
                "Kcal_Goal": [target_kcal], "Prot_Goal": [target_prot], 
                "Glu_Goal": [target_glu], "Lip_Goal": [target_lip]
            })
            utils.save_data(new_goals, utils.GOALS_FILE)
            st.success("Objectifs mis à jour !")
            st.rerun()

    st.markdown("---")

    # ====================================================
    # 2. SUIVI JOURNALIER (PROGRESS BAR)
    # ====================================================
    col_date, col_viz = st.columns([1, 2])
    with col_date:
        selected_date = st.date_input("Date", datetime.today(), key="n_date")
        selected_ts = pd.to_datetime(selected_date)
    
    # Filtrage du jour
    daily_log = df_log[df_log['Date'] == selected_ts]
    
    # Sommes du jour
    consumed = {
        "Kcal": daily_log['Kcal_Total'].sum(),
        "Prot": daily_log['Prot_Total'].sum(),
        "Glu": daily_log['Glu_Total'].sum(),
        "Lip": daily_log['Lip_Total'].sum()
    }
    
    # Fonction d'affichage de barre
    def display_progress(label, value, goal, color_hex="#10B981"):
        pct = min(value / goal, 1.0) if goal > 0 else 0
        delta = goal - value
        
        # Texte dynamique
        txt_val = f"{int(value)} / {int(goal)}"
        if label != "Kcal": txt_val += "g"
            
        c1, c2 = st.columns([3, 1])
        with c1:
            st.write(f"**{label}** : {txt_val}")
            st.progress(pct)
        with c2:
            # Indicateur restant
            if delta >= 0:
                st.caption(f"Reste : {int(delta)}")
            else:
                st.markdown(f"<span style='color:red'>+{int(abs(delta))} !</span>", unsafe_allow_html=True)

    with col_viz:
        st.markdown("### Bilan Journalier")
        display_progress("Kcal", consumed["Kcal"], current_goals["Kcal"])
        
        # Petit layout pour les macros en dessous
        c_m1, c_m2, c_m3 = st.columns(3)
        c_m1.metric("Prot", f"{int(consumed['Prot'])}g", f"{int(consumed['Prot']-current_goals['Prot'])}g")
        c_m2.metric("Glu", f"{int(consumed['Glu'])}g", f"{int(consumed['Glu']-current_goals['Glu'])}g")
        c_m3.metric("Lip", f"{int(consumed['Lip'])}g", f"{int(consumed['Lip']-current_goals['Lip'])}g")

    st.markdown("---")

    # ====================================================
    # 3. AJOUT REPAS & DB (Le reste inchangé mais réintégré)
    # ====================================================
    
    # --- AJOUT ALIMENT DB ---
    with st.expander("➕ Base de données Aliments"):
        c1, c2, c3 = st.columns([2, 1, 1])
        new_name = c1.text_input("Nom aliment")
        ref_weight = c2.number_input("Pour (g)", value=100, step=10)
        new_kcal = c3.number_input("Kcal", step=1)
        c4, c5, c6 = st.columns(3)
        new_prot = c4.number_input("Prot (g)", step=0.1)
        new_carb = c5.number_input("Glu (g)", step=0.1)
        new_fat = c6.number_input("Lip (g)", step=0.1)
        
        if st.button("Ajouter à la base"):
            if new_name and new_name not in df_food_db['Aliment'].values:
                new_row = pd.DataFrame({
                    "Aliment": [new_name], "Kcal": [new_kcal], "Proteines": [new_prot], 
                    "Glucides": [new_carb], "Lipides": [new_fat], "Poids_Ref": [ref_weight]
                })
                df_food_db = pd.concat([df_food_db, new_row], ignore_index=True)
                utils.save_data(df_food_db, utils.FOOD_DB_FILE)
                st.success(f"{new_name} ajouté !")
                st.rerun()

    # --- ENREGISTRER REPAS ---
    st.subheader("🍽️ Manger")
    if df_food_db.empty:
        st.warning("Base vide.")
    else:
        c_when, c_what = st.columns([1, 2])
        meal_type = c_when.selectbox("Repas", ["Petit-déjeuner", "Déjeuner", "Dîner", "Snack"])
        food_choice = c_what.selectbox("Aliment", df_food_db['Aliment'].unique())
        
        c_how_much, c_btn = st.columns([2, 1])
        ref_info = df_food_db[df_food_db['Aliment'] == food_choice].iloc[0]
        ref_w = ref_info.get('Poids_Ref', 100)
        
        qty_g = c_how_much.number_input(f"Poids (g)", value=float(ref_w), step=10.0)
        
        with c_btn:
            st.write("")
            st.write("")
            if st.button("Ajouter", use_container_width=True):
                ratio = qty_g / ref_w
                new_entry = pd.DataFrame({
                    "Date": [selected_ts], "Repas": [meal_type], "Aliment": [food_choice],
                    "Poids_Conso": [qty_g],
                    "Kcal_Total": [ref_info['Kcal'] * ratio],
                    "Prot_Total": [ref_info['Proteines'] * ratio],
                    "Glu_Total": [ref_info['Glucides'] * ratio],
                    "Lip_Total": [ref_info['Lipides'] * ratio]
                })
                df_log = pd.concat([df_log, new_entry], ignore_index=True)
                utils.save_data(df_log, utils.NUTRITION_LOG_FILE)
                st.success("Ajouté !")
                st.rerun()

    # --- DETAILS PAR REPAS ---
    for meal in ["Petit-déjeuner", "Déjeuner", "Dîner", "Snack"]:
        m_data = daily_log[daily_log['Repas'] == meal]
        with st.expander(f"{meal} ({int(m_data['Kcal_Total'].sum())} Kcal)", expanded=(not m_data.empty)):
            if not m_data.empty:
                disp = m_data[["Aliment", "Poids_Conso", "Kcal_Total", "Prot_Total", "Glu_Total", "Lip_Total"]].copy()
                disp.columns = ["Aliment", "g", "Kcal", "P", "G", "L"]
                st.dataframe(disp, use_container_width=True)
                if st.button(f"Effacer dernier ({meal})", key=f"del_{meal}"):
                    df_log = df_log.drop(m_data.index[-1])
                    utils.save_data(df_log, utils.NUTRITION_LOG_FILE)
                    st.rerun()
