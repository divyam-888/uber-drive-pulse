import streamlit as st
import pandas as pd
import time
import altair as alt
from datetime import datetime
import threading
from simulator import run_simulator 

# ==========================================
# 1. PAGE CONFIGURATION & ARCHITECTURE
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
        position: fixed;
        bottom: 20px;
        left: 0;
        width: 100%;
        text-align: center;
        color: #666666;
        font-family: 'Helvetica Neue', sans-serif;
        font-size: 14px;
        letter-spacing: 1px;
    }
    div[data-testid="metric-container"] {
        background-color: #1a1a1a;
        border: 1px solid #333;
        padding: 15px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. DATA LAYER
# ==========================================
def load_data():
    try:
        fin_df = pd.read_csv("data/earnings_velocity_log.csv")
        safe_df = pd.read_csv("data/flagged_moments.csv")
        goals_df = pd.read_csv("data/driver_goals.csv")
        trips_df = pd.read_csv("data/trips.csv")
        return fin_df, safe_df, goals_df.iloc[0] if not goals_df.empty else None, trips_df
    except (FileNotFoundError, pd.errors.EmptyDataError):
        time.sleep(0.1)
        return pd.DataFrame(), pd.DataFrame(), None, pd.DataFrame()

# ==========================================
# 3. UI COMPONENTS
# ==========================================
def render_live_shift(fin_df, goal):
    st.markdown("<h1 style='text-align: center; font-weight: 600;'>Uber <span style='color: #276ef1;'>Drive Pulse</span></h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #888;'>Live Shift Companion • Alex Kumar</p>", unsafe_allow_html=True)
    st.divider()
    
    if fin_df.empty or goal is None:
        st.info("📡 Waiting for connection to driver's vehicle... Click 'Start Fresh Simulation' in the sidebar.")
        return

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

def render_post_shift(fin_df, safe_df, goal, trips_df, is_syncing):
    st.markdown("### 📊 Post-Shift Analytics")
    
    if is_syncing:
        st.warning("⚠️ **Live Sync is currently active.** If you want to interact with the charts and filters smoothly without the page reloading, toggle 'Live Sync' OFF in the sidebar.")
    
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
                    alt.Tooltip('start_time', title='Started At'),
                    alt.Tooltip('end_time', title='Ended At')
                ]
            ).interactive()
            
            st.altair_chart(actual_line + ideal_line + points, use_container_width=True)
            st.caption("Hover over the white dots to see specific trip details.")
        else:
            st.write("No financial data available.")

    with col_safety:
        st.markdown("#### Safety & Telemetry")
        score = 100
        if not safe_df.empty:
            # Clean strings to prevent matching bugs
            safe_df['severity_clean'] = safe_df['severity'].astype(str).str.strip().str.upper()
            
            highs = len(safe_df[safe_df['severity_clean'] == 'HIGH'])
            meds = len(safe_df[safe_df['severity_clean'] == 'MEDIUM'])
            score = max(0, 100 - (highs * 10) - (meds * 5))
            
        color = "green" if score > 85 else "orange" if score > 70 else "red"
        st.markdown(f"**Overall Safety Score:** :{color}[{score}/100]")
        
        if not safe_df.empty:
            st.markdown("##### Filter Events")
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                sev_filter = st.multiselect("Severity", ["HIGH", "MEDIUM", "LOW"], default=["HIGH", "MEDIUM"])
            with f_col2:
                type_filter = st.multiselect("Event Type", ["Motion", "Audio", "Conflict"], default=["Motion", "Audio", "Conflict"])
            
            # --- STRICT FILTERING LOGIC ---
            if not sev_filter:
                # If nothing is selected, force an empty dataframe
                filtered_df = pd.DataFrame(columns=safe_df.columns)
            else:
                filtered_df = safe_df[safe_df['severity_clean'].isin(sev_filter)].copy()
            
            if not filtered_df.empty:
                if not type_filter:
                    filtered_df = pd.DataFrame(columns=filtered_df.columns)
                else:
                    def match_type(context_str):
                        context_str = str(context_str).lower()
                        if "motion" in context_str and "audio" in context_str: return "Conflict"
                        if "motion" in context_str: return "Motion"
                        if "audio" in context_str: return "Audio"
                        return "Other"
                        
                    filtered_df['event_category'] = filtered_df['context'].apply(match_type)
                    filtered_df = filtered_df[filtered_df['event_category'].isin(type_filter)]
            
            st.markdown("##### Event Log")
            with st.container(height=350):
                if filtered_df.empty:
                    st.success("No events match your current filters.")
                else:
                    for idx, row in filtered_df.sort_values(by='timestamp').iterrows(): 
                        sev = row['severity_clean']
                        icon = "🚨" if sev == "HIGH" else "⚠️" if sev == "MEDIUM" else "ℹ️"
                        with st.expander(f"{icon} {sev} | {row['timestamp'].split(' ')[1]} | {row['trip_id']}"):
                            st.markdown(f"**Flag:** {row['flag_type'].replace('_', ' ').title()}")
                            st.markdown(f"**Details:** {row['explanation']}")
                            st.caption(f"Raw Context: {row['context']}")
        else:
            st.success("No critical safety events flagged today. Great driving!")

# ==========================================
# 4. MAIN EVENT LOOP & SESSION STATE
# ==========================================
def main():
    if 'sim_running' not in st.session_state:
        st.session_state.sim_running = False

    with st.sidebar:
        st.markdown("### Control Panel")
        st.write("Welcome to the Uber Drive Pulse demo.")
        
        if st.button("▶️ Start Fresh Simulation", type="primary", use_container_width=True):
            # Wipe files clean
            pd.DataFrame(columns=["log_id", "driver_id", "trip_id", "timestamp", "cumulative_earnings", "elapsed_hours", "trips_completed", "current_velocity", "required_velocity", "velocity_delta", "avg_earning_per_trip", "est_trips_remaining", "forecast_status"]).to_csv("data/earnings_velocity_log.csv", index=False)
            pd.DataFrame(columns=["flag_id", "trip_id", "driver_id", "timestamp", "elapsed_seconds", "flag_type", "severity", "explanation", "context"]).to_csv("data/flagged_moments.csv", index=False)
            
            sim_thread = threading.Thread(target=run_simulator, daemon=True)
            sim_thread.start()
            
            st.session_state.sim_running = True
            st.rerun()

        st.divider()
        auto_refresh = st.toggle("Live Sync (Auto-Refresh)", value=st.session_state.sim_running)

    fin_df, safe_df, goal, trips_df = load_data()
    
    # --- AUTO-KILL SWITCH ---
    # If the simulation hits 9 trips and is achieved, turn off the live sync automatically
    if auto_refresh and not fin_df.empty:
        if len(fin_df) >= 8 and str(fin_df.iloc[-1]['forecast_status']).upper() == "ACHIEVED":
            st.session_state.sim_running = False
            auto_refresh = False
            st.sidebar.success("✅ Simulation Finished! Live Sync disabled.")
    
    tab_live, tab_analytics = st.tabs(["🚗 Live Shift", "📊 Pit Stop Analytics"])
    
    with tab_live:
        render_live_shift(fin_df, goal)
        
    with tab_analytics:
        render_post_shift(fin_df, safe_df, goal, trips_df, is_syncing=auto_refresh)

    # Cloud-safe polling rate (2.0 seconds)
    if auto_refresh:
        time.sleep(2.0) 
        st.rerun()

if __name__ == "__main__":
    main()