import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
import utils

# --- CALLBACKS ---
def update_water_callback(amount):
    selected_d = st.session_state.get('h_date', datetime.today())
    selected_ts = pd.to_datetime(selected_d)
    df = utils.load_data(utils.HABITS_FILE, ["Date", "Habit", "Value", "Goal"])
    mask = (df['Date'] == selected_ts) & (df['Habit'] == 'Eau')
    
    if df[mask].empty:
        new_val = max(0.0, 0.0 + amount)
        new_row = pd.DataFrame({"Date": [selected_ts], "Habit": ["Eau"], "Value": [new_val], "Goal": [2.0]})
        df = pd.concat([df, new_row], ignore_index=True)
    else:
        idx = df[mask].index[0]
        current_val = df.at[idx, 'Value']
        new_val = round(max(0.0, current_val + amount), 2)
        df.at[idx, 'Value'] = new_val
    utils.save_data(df, utils.HABITS_FILE)

def update_goal_callback():
    selected_d = st.session_state.get('h_date', datetime.today())
    selected_ts = pd.to_datetime(selected_d)
    new_goal = st.session_state.get('h_goal_input', 2.0)
    df = utils.load_data(utils.HABITS_FILE, ["Date", "Habit", "Value", "Goal"])
    mask = (df['Date'] == selected_ts) & (df['Habit'] == 'Eau')
    if df[mask].empty:
        new_row = pd.DataFrame({"Date": [selected_ts], "Habit": ["Eau"], "Value": [0.0], "Goal": [new_goal]})
        df = pd.concat([df, new_row], ignore_index=True)
    else:
        idx = df[mask].index[0]
        df.at[idx, 'Goal'] = round(new_goal, 2)
    utils.save_data(df, utils.HABITS_FILE)

def show():
    st.header("💧 Hydratation")
    
    df_habits = utils.load_data(utils.HABITS_FILE, ["Date", "Habit", "Value", "Goal"])
    selected_date_ts = pd.to_datetime(st.date_input("Date", datetime.today(), key="h_date"))
    mask = (df_habits['Date'] == selected_date_ts) & (df_habits['Habit'] == 'Eau')
    
    if df_habits[mask].empty: display_water, display_goal = 0.0, 2.0
    else: display_water, display_goal = df_habits[mask].iloc[0]['Value'], df_habits[mask].iloc[0]['Goal']

    col_ring, col_ctrl = st.columns([1, 2])
    
    with col_ring:
         percent = int((display_water/display_goal)*100) if display_goal > 0 else 0
         st.metric("HYDRATATION", f"{percent}%", f"{display_water:.2f}L / {display_goal:.1f}L")
    
    with col_ctrl:
        st.write("Ajouter consommation (25cl) :")
        c_minus, c_plus = st.columns(2)
        with c_minus: st.button("➖", on_click=update_water_callback, args=(-0.25,), use_container_width=True)
        with c_plus: st.button("➕", on_click=update_water_callback, args=(0.25,), use_container_width=True)
        
        st.write("Objectif (L) :")
        st.number_input("Objectif", value=float(display_goal), step=0.1, format="%.1f", key="h_goal_input", label_visibility="collapsed", on_change=update_goal_callback)

    st.progress(min(display_water / display_goal, 1.0) if display_goal > 0 else 0)

    st.markdown("---")
    st.markdown("### HISTORIQUE SEMAINE")
    
    df_water_hist = df_habits[df_habits['Habit'] == 'Eau'].copy().sort_values(by='Date').tail(7)
    if not df_water_hist.empty:
        bars = alt.Chart(df_water_hist).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
            x=alt.X('Date', axis=alt.Axis(format='%d', title=None, labelColor='#888')),
            y=alt.Y('Value', title=None),
            color=alt.condition(
                alt.datum.Value >= alt.datum.Goal, alt.value('#10B981'), alt.value('#374151')
            ),
            tooltip=[alt.Tooltip('Date', format='%d/%m'), alt.Tooltip('Value', format='.2f'), alt.Tooltip('Goal', format='.1f')]
        )
        line = alt.Chart(df_water_hist).mark_rule(color='#10B981', strokeDash=[2,2]).encode(y='Goal')
        st.altair_chart((bars + line).properties(height=200, background='transparent'), use_container_width=True)
