import streamlit as st
import pandas as pd
import altair as alt
import utils
from datetime import datetime

# --- FONCTION GRAPHIQUE DONUT (CAMEMBERT) ---
def make_donut_chart(df_macros):
    # df_macros doit avoir colonnes: ['Category', 'Value', 'Color']
    base = alt.Chart(df_macros).encode(
        theta=alt.Theta("Value", stack=True)
    )
    pie = base.mark_arc(outerRadius=120, innerRadius=80).encode(
        color=alt.Color("Category", scale=alt.Scale(domain=df_macros["Category"].tolist(), range=df_macros["Color"].tolist()), legend=None),
        tooltip=["Category", "Value"]
    )
    text = base.mark_text(radius=140).encode(
        text=alt.Text("Value", format=".1f"),
        order=alt.Order("Category"),
        color=alt.value("white")
    )
    return (pie + text).properties(height=300, background='transparent')

def show():
    st.header("🥗 Nutrition & Macros")
    
    # 1. CHARGEMENT
    # Nouvelles colonnes : Marque, Unite
    df_food_db = utils.load_data(utils.FOOD_DB_FILE, ["Marque", "Aliment", "Unite", "Portion_Ref", "Kcal", "Proteines", "Glucides", "Lipides"])
    df_log = utils.load_data(utils.NUTRITION_LOG_FILE, ["Date", "Repas", "Marque", "Aliment", "Quantite", "Unite", "Kcal_Total", "Prot_Total", "Glu_Total", "Lip_Total"])
    df_goals = utils.load_data(utils.GOALS_FILE, ["Kcal_Goal", "Prot_Goal", "Glu_Goal", "Lip_Goal"])
    
    # Objectifs par défaut
    if df_goals.empty: current_goals = {"Kcal": 2000, "Prot": 150, "Glu": 200, "Lip": 70}
    else:
        last_g = df_goals.iloc[-1]
        current_goals = {"Kcal": last_g['Kcal_Goal'], "Prot": last_g['Prot_Goal'], "Glu": last_g['Glu_Goal'], "Lip": last_g['Lip_Goal']}

    # ====================================================
    # SECTION 1 : VISUALISATION (TABLEAU DE BORD)
    # ====================================================
    col_date, col_summary = st.columns([1, 2])
    with col_date: 
        selected_date = pd.to_datetime(st.date_input("Date", datetime.today(), key="n_date"))
    
    daily_log = df_log[df_log['Date'] == selected_date]
    
    # Calculs Consommation
    cons = {
        "Kcal": daily_log['Kcal_Total'].sum(),
        "Prot": daily_log['Prot_Total'].sum(),
        "Glu": daily_log['Glu_Total'].sum(),
        "Lip": daily_log['Lip_Total'].sum()
    }
    
    with col_summary:
        st.markdown("### Synthèse Journalière")
        # Barre Kcal
        k_pct = min(cons["Kcal"] / current_goals["Kcal"], 1.0)
        st.write(f"**Calories** : {int(cons['Kcal'])} / {int(current_goals['Kcal'])} kcal")
        st.progress(k_pct)

    # GRAPHIQUES MACROS
    if cons["Kcal"] > 0:
        c_chart, c_details = st.columns([1, 1])
        
        with c_chart:
            # Préparation données pour Altair
            macro_data = pd.DataFrame([
                {"Category": "Protéines", "Value": cons["Prot"], "Color": "#10B981"}, # Vert
                {"Category": "Glucides", "Value": cons["Glu"], "Color": "#3B82F6"},  # Bleu
                {"Category": "Lipides", "Value": cons["Lip"], "Color": "#F59E0B"}    # Jaune/Orange
            ])
            st.altair_chart(make_donut_chart(macro_data), use_container_width=True)
            
        with c_details:
            st.write("") # Espacement
            st.write("")
            st.metric("Protéines", f"{int(cons['Prot'])}g", f"{int(cons['Prot'] - current_goals['Prot'])}g target")
            st.metric("Glucides", f"{int(cons['Glu'])}g", f"{int(cons['Glu'] - current_goals['Glu'])}g target")
            st.metric("Lipides", f"{int(cons['Lip'])}g", f"{int(cons['Lip'] - current_goals['Lip'])}g target")
    else:
        st.info("Aucune donnée pour cette journée.")

    st.markdown("---")

    # ====================================================
    # SECTION 2 : AJOUT ALIMENT (BASE DE DONNÉES)
    # ====================================================
    with st.expander("➕ Créer un nouvel aliment (Base de Données)"):
        c1, c2 = st.columns(2)
        n_marque = c1.text_input("Marque (facultatif)")
        n_name = c2.text_input("Nom de l'aliment")
        
        c3, c4 = st.columns(2)
        n_unit = c3.selectbox("Type d'unité", ["grammes", "unité(s)", "cuillère(s) à soupe", "cuillère(s) à café", "portion(s)", "ml"])
        
        # Label dynamique pour guider l'utilisateur
        lbl_ref = "Pour 100g" if n_unit in ["grammes", "ml"] else f"Pour 1 {n_unit[:-3] if len(n_unit)>3 else n_unit}"
        n_ref_qty = c4.number_input(f"Quantité de référence ({lbl_ref})", value=100.0 if n_unit in ["grammes", "ml"] else 1.0)

        st.markdown(f"**Valeurs nutritionnelles pour {n_ref_qty} {n_unit} :**")
        k1, k2, k3, k4 = st.columns(4)
        n_kcal = k1.number_input("Kcal", step=1)
        n_p = k2.number_input("Prot (g)", step=0.1)
        n_g = k3.number_input("Glu (g)", step=0.1)
        n_l = k4.number_input("Lip (g)", step=0.1)
        
        if st.button("Sauvegarder dans la base"):
            if n_name:
                # Création d'une clé unique pour éviter doublons (Marque + Nom)
                full_name = f"{n_marque} - {n_name}" if n_marque else n_name
                
                # Vérif doublon simple sur le nom combiné n'est pas parfaite mais suffisante ici
                exists = False
                if not df_food_db.empty:
                    # On check si une ligne a la même marque et nom
                    exists = ((df_food_db['Aliment'] == n_name) & (df_food_db['Marque'] == n_marque)).any()

                if not exists:
                    row = pd.DataFrame({
                        "Marque": [n_marque], "Aliment": [n_name], "Unite": [n_unit], "Portion_Ref": [n_ref_qty],
                        "Kcal": [n_kcal], "Proteines": [n_p], "Glucides": [n_g], "Lipides": [n_l]
                    })
                    utils.save_data(pd.concat([df_food_db, row], ignore_index=True), utils.FOOD_DB_FILE)
                    st.success(f"{full_name} ajouté !")
                    st.rerun()
                else:
                    st.error("Cet aliment existe déjà.")

    # ====================================================
    # SECTION 3 : CONSOMMATION (LOG)
    # ====================================================
    st.subheader("🍽️ Ajouter un repas")
    
    if df_food_db.empty:
        st.warning("La base d'aliments est vide.")
    else:
        # Création d'une liste déroulante jolie : "Marque - Aliment"
        df_food_db['Display'] = df_food_db.apply(lambda x: f"{x['Marque']} - {x['Aliment']}" if pd.notnull(x['Marque']) and x['Marque'] != "" else x['Aliment'], axis=1)
        
        c_when, c_what = st.columns([1, 2])
        m_type = c_when.selectbox("Repas", ["Petit-déjeuner", "Déjeuner", "Dîner", "Snack"])
        f_choice_display = c_what.selectbox("Rechercher un aliment", df_food_db['Display'].unique())
        
        # Retrouver les infos de l'aliment choisi
        info = df_food_db[df_food_db['Display'] == f_choice_display].iloc[0]
        
        # Interface dynamique selon l'unité
        c_qty, c_btn = st.columns([2, 1])
        
        unit_label = info['Unite']
        # Si c'est grammes, step de 10, sinon step de 1 ou 0.5
        step_val = 10.0 if unit_label in ["grammes", "ml"] else 0.5
        default_val = float(info['Portion_Ref'])
        
        user_qty = c_qty.number_input(f"Quantité ({unit_label})", value=default_val, step=step_val)
        
        with c_btn:
            st.write("")
            st.write("")
            if st.button("Manger", use_container_width=True):
                # LE CALCUL UNIVERSEL
                # Ratio = Ce que je mange / La portion de référence enregistrée
                ratio = user_qty / info['Portion_Ref']
                
                new_entry = pd.DataFrame({
                    "Date": [selected_date],
                    "Repas": [m_type],
                    "Marque": [info['Marque']],
                    "Aliment": [info['Aliment']],
                    "Quantite": [user_qty],
                    "Unite": [unit_label],
                    "Kcal_Total": [info['Kcal'] * ratio],
                    "Prot_Total": [info['Proteines'] * ratio],
                    "Glu_Total": [info['Glucides'] * ratio],
                    "Lip_Total": [info['Lipides'] * ratio]
                })
                df_log = pd.concat([df_log, new_entry], ignore_index=True)
                utils.save_data(df_log, utils.NUTRITION_LOG_FILE)
                st.success("Ajouté !")
                st.rerun()

    # ====================================================
    # SECTION 4 : LISTE DÉTAILLÉE
    # ====================================================
    for m in ["Petit-déjeuner", "Déjeuner", "Dîner", "Snack"]:
        d = daily_log[daily_log['Repas'] == m]
        with st.expander(f"{m} ({int(d['Kcal_Total'].sum())} kcal)", expanded=(not d.empty)):
            if not d.empty:
                # Affichage propre pour l'utilisateur
                disp = d.copy()
                # On crée une colonne description ex: "100 grammes" ou "2 biscuits"
                disp['Conso'] = disp.apply(lambda x: f"{x['Quantite']:g} {x['Unite']}", axis=1)
                
                # On affiche Marque - Aliment
                disp['Item'] = disp.apply(lambda x: f"{x['Marque']} - {x['Aliment']}" if pd.notnull(x['Marque']) and x['Marque'] != "" else x['Aliment'], axis=1)
                
                st.dataframe(
                    disp[["Item", "Conso", "Kcal_Total", "Prot_Total", "Glu_Total", "Lip_Total"]].rename(
                        columns={"Kcal_Total": "Kcal", "Prot_Total": "Prot", "Glu_Total": "Glu", "Lip_Total": "Lip"}
                    ), 
                    use_container_width=True,
                    hide_index=True
                )
                
                if st.button(f"Supprimer dernier ajout ({m})", key=f"del_{m}"):
                    utils.save_data(df_log.drop(d.index[-1]), utils.NUTRITION_LOG_FILE)
                    st.rerun()
