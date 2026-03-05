import streamlit as st
import pandas as pd
import time
import altair as alt
from datetime import datetime
import threading

# Import your backend engines!
from simulator import run_simulator 
from generate_synthetic_data import generate_data

# ==========================================
# 1. PAGE CONFIGURATION & CSS
# ==========================================
st.set_page_config(page_title="Uber Drive Pulse", page_icon="⬛", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stProgress .st-bo {background-color: #276ef1;}
    .css-1v0mbdj.etr89bj1 {border-radius: 12px;}
    .uber-footer {
        position: fixed; bottom: 20px; left: 0; width: 100%;
        text-align: center; color: #666666; font-family: 'Helvetica Neue', sans-serif;
        font-size: 14px; letter-spacing: 1px;
    }
    div[data-testid="metric-container"] {
        background-color: #1a1a1a; border: 1px solid #333;
        padding: 15px; border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. DATA LAYER (Fail-Safe Loading)
# ==========================================
def load_data():
    try:
        fin_df = pd.read_csv("data/earnings_velocity_log.csv")
        safe_df = pd.read_csv("data/flagged_moments.csv")
        goals_df = pd.read_csv("data/driver_goals.csv")
        trips_df = pd.read_csv("data/trips.csv")
        return fin_df, safe_df, goals_df.iloc[0] if not goals_df.empty else None, trips_df
    except (FileNotFoundError, pd.errors.EmptyDataError):
        # If files are missing or locked, return empty state
        return pd.DataFrame(), pd.DataFrame(), None, pd.DataFrame()

# ==========================================
# 3. UI COMPONENTS
# ==========================================
def render_live_shift(fin_df, goal):
    st.markdown("<h1 style='text-align: center; font-weight: 600;'>Uber <span style='color: #276ef1;'>Drive Pulse</span></h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #888;'>Live Shift Companion • Alex Kumar</p>", unsafe_allow_html=True)
    st.divider()
    
    latest = fin_df.iloc[-1]
    target = float(goal['target_earnings'])
    current = float(latest['cumulative_earnings'])
    progress = min(current / target, 1.0)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Today's Earnings", value=f"${current:.0f}", delta=f"Target: ${target:.0f}", delta_color="off")
    with col2:
        st.metric(label="Current Pace", value=f"${latest['current_velocity']:.0f}/hr")
    with col3:
        status = str(latest['forecast_status']).upper()
        color = "🟢" if status in ["ACHIEVED", "AHEAD"] else "🟡" if status == "ON_TRACK" else "🔴"
        st.metric(label="Forecast Status", value=f"{color} {status}")

    st.markdown("<br>", unsafe_allow_html=True)
    st.progress(progress)
    st.caption(f"Estimated {latest['est_trips_remaining']} trips remaining to hit target.")
    st.markdown("<div class='uber-footer'><b>Uber</b> Engineering Hackathon 2026</div>", unsafe_allow_html=True)

def render_post_shift(fin_df, safe_df, goal, trips_df):
    st.markdown("### 📊 Post-Shift Analytics")
    
    if st.session_state.sim_running:
        st.warning("⚠️ **Live Sync Active:** The dashboard is updating in real-time. Wait for the shift to end to freely interact with the charts.")
    
    col_chart, col_safety = st.columns([1.8, 1.2])

    with col_chart:
        st.markdown("#### Earnings Pace Chart")
        if not fin_df.empty and goal is not None and not trips_df.empty:
            chart_data = pd.merge(fin_df, trips_df, on="trip_id", how="left")
            target_earnings = float(goal['target_earnings'])
            target_hours = float(goal['target_hours'])
            ideal_slope = target_earnings / target_hours
            chart_data['ideal_earnings'] = chart_data['elapsed_hours'] * ideal_slope
            
            base = alt.Chart(chart_data).encode(x=alt.X('elapsed_hours', title='Hours Driven'))
            actual_line = base.mark_line(color='#276ef1', strokeWidth=3).encode(y=alt.Y('cumulative_earnings', title='Earnings ($)'))
            ideal_line = base.mark_line(color='gray', strokeDash=[5, 5], opacity=0.5).encode(y='ideal_earnings')
            
            points = base.mark_circle(size=80, color='white', opacity=1).encode(
                y='cumulative_earnings',
                tooltip=[
                    alt.Tooltip('trip_id', title='Trip ID'),
                    alt.Tooltip('fare', title='Fare ($)'),
                    alt.Tooltip('duration_min', title='Duration (min)'),
                    alt.Tooltip('start_time', title='Started At')
                ]
            ).interactive()
            
            st.altair_chart(actual_line + ideal_line + points, use_container_width=True)
        else:
            st.write("No financial data available.")

    with col_safety:
        st.markdown("#### Safety & Telemetry")
        if safe_df.empty:
            st.success("No safety events logged yet.")
            return

        # 1. Clean data for strict matching
        safe_df['severity_clean'] = safe_df['severity'].astype(str).str.strip().str.upper()
        
        # 2. Calculate Score
        highs = len(safe_df[safe_df['severity_clean'] == 'HIGH'])
        meds = len(safe_df[safe_df['severity_clean'] == 'MEDIUM'])
        score = max(0, 100 - (highs * 10) - (meds * 5))
        color = "green" if score > 85 else "orange" if score > 70 else "red"
        st.markdown(f"**Overall Safety Score:** :{color}[{score}/100]")
        
        # 3. Filter UI
        st.markdown("##### Filter Events")
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            sev_filter = st.multiselect("Severity", ["HIGH", "MEDIUM", "LOW"], default=["HIGH", "MEDIUM"])
        with f_col2:
            type_filter = st.multiselect("Event Type", ["Motion", "Audio", "Conflict"], default=["Motion", "Audio", "Conflict"])
        
        # 4. STRICT FILTERING LOGIC
        filtered_df = safe_df.copy()
        
        # Filter by Severity
        if not sev_filter:
            filtered_df = pd.DataFrame(columns=filtered_df.columns) # Empty it
        else:
            filtered_df = filtered_df[filtered_df['severity_clean'].isin(sev_filter)]
            
        # Filter by Type
        if not filtered_df.empty:
            if not type_filter:
                filtered_df = pd.DataFrame(columns=filtered_df.columns) # Empty it
            else:
                def get_cat(ctx):
                    ctx = str(ctx).lower()
                    if "motion" in ctx and "audio" in ctx: return "Conflict"
                    if "motion" in ctx: return "Motion"
                    if "audio" in ctx: return "Audio"
                    return "Other"
                filtered_df['category'] = filtered_df['context'].apply(get_cat)
                filtered_df = filtered_df[filtered_df['category'].isin(type_filter)]
        
        # 5. Render Log
        st.markdown("##### Event Log")
        with st.container(height=350):
            if filtered_df.empty:
                st.info("No events match your current filters.")
            else:
                for idx, row in filtered_df.sort_values(by='timestamp').iterrows(): 
                    sev = row['severity_clean']
                    icon = "🚨" if sev == "HIGH" else "⚠️" if sev == "MEDIUM" else "ℹ️"
                    with st.expander(f"{icon} {sev} | {str(row['timestamp']).split(' ')[1]} | {row['trip_id']}"):
                        st.markdown(f"**Flag:** {str(row['flag_type']).replace('_', ' ').title()}")
                        st.markdown(f"**Details:** {row['explanation']}")
                        st.caption(f"Raw Context: {row['context']}")

# ==========================================
# 4. MAIN EVENT LOOP & ROUTING
# ==========================================
def main():
    if 'sim_running' not in st.session_state:
        st.session_state.sim_running = False

    fin_df, safe_df, goal, trips_df = load_data()

    # --- AUTO-KILL SWITCH ---
    # Stops the infinite reload loop exactly when the shift ends
    if st.session_state.sim_running and not fin_df.empty:
        if len(fin_df) >= 8 and str(fin_df.iloc[-1]['forecast_status']).upper() == "ACHIEVED":
            st.session_state.sim_running = False
            st.toast("✅ Shift Completed! Analytics unlocked.")

    tab_live, tab_analytics = st.tabs(["🚗 Live Shift", "📊 Pit Stop Analytics"])
    
    with tab_live:
        if fin_df.empty or goal is None:
            # --- THE SELF-HEALING COLD START VIEW ---
            st.markdown("<h1 style='text-align: center; margin-top: 50px;'>Uber <span style='color: #276ef1;'>Drive Pulse</span></h1>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #888;'>System Offline. No active shift data found.</p>", unsafe_allow_html=True)
            
            colA, colB, colC = st.columns([1, 2, 1])
            with colB:
                if st.button("▶️ Initialize System & Start Shift", type="primary", use_container_width=True):
                    with st.spinner("Generating Universe and calibrating sensors..."):
                        # 1. Self-Heal: Build the data folder from scratch
                        generate_data() 
                        time.sleep(1) # Give the cloud OS time to write the files
                        
                        # 2. Start the simulation
                        threading.Thread(target=run_simulator, daemon=True).start()
                        
                        # 3. Trigger the UI to start polling
                        st.session_state.sim_running = True
                        st.rerun()
        else:
            render_live_shift(fin_df, goal)
            
            # Allow manual override to stop the simulation
            if st.session_state.sim_running:
                if st.button("⏹ Stop Live Sync"):
                    st.session_state.sim_running = False
                    st.rerun()
        
    with tab_analytics:
        render_post_shift(fin_df, safe_df, goal, trips_df)

    # The safe 2-second cloud polling loop
    if st.session_state.sim_running:
        time.sleep(2.0)
        st.rerun()

if __name__ == "__main__":
    main()