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

# CSS Injection for Premium Uber/Apple Aesthetics
st.markdown("""
    <style>
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Uber Brand Styling */
    .stProgress .st-bo {background-color: #276ef1;}
    .css-1v0mbdj.etr89bj1 {border-radius: 12px;} /* Round image corners */
    
    /* Custom Footer Styling */
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
    
    /* Sleek Metric Cards */
    div[data-testid="metric-container"] {
        background-color: #1a1a1a;
        border: 1px solid #333;
        padding: 15px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. DATA LAYER (Polling the CSVs)
# ==========================================
def load_data():
    """Reads all CSVs. Fails gracefully to prevent File Lock errors during demo."""
    try:
        fin_df = pd.read_csv("data/earnings_velocity_log.csv")
        safe_df = pd.read_csv("data/flagged_moments.csv")
        goals_df = pd.read_csv("data/driver_goals.csv")
        trips_df = pd.read_csv("data/trips.csv") # New: Loaded for chart tooltips!
        return fin_df, safe_df, goals_df.iloc[0] if not goals_df.empty else None, trips_df
    except (FileNotFoundError, pd.errors.EmptyDataError):
        time.sleep(0.1)
        return pd.DataFrame(), pd.DataFrame(), None, pd.DataFrame()

# ==========================================
# 3. UI COMPONENTS
# ==========================================
def render_live_shift(fin_df, goal):
    """STATE A: Distraction-free live driving interface."""
    
    # Premium Header
    st.markdown("<h1 style='text-align: center; font-weight: 600;'>Uber <span style='color: #276ef1;'>Drive Pulse</span></h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #888;'>Live Shift Companion • Alex Kumar</p>", unsafe_allow_html=True)
    st.divider()
    
    if fin_df.empty or goal is None:
        st.info("📡 Waiting for connection to driver's vehicle...")
        return

    latest = fin_df.iloc[-1]
    target = float(goal['target_earnings'])
    current = float(latest['cumulative_earnings'])
    progress = min(current / target, 1.0)
    
    # Minimalist Metric Row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Today's Earnings", value=f"${current:.0f}", delta=f"Target: ${target:.0f}", delta_color="off")
    with col2:
        st.metric(label="Current Pace", value=f"${latest['current_velocity']:.0f}/hr")
    with col3:
        status = str(latest['forecast_status']).upper()
        color = "🟢" if status == "ACHIEVED" or status == "AHEAD" else "🟡" if status == "ON_TRACK" else "🔴"
        st.metric(label="Forecast Status", value=f"{color} {status}")

    # Massive, satisfying progress bar
    st.markdown("<br>", unsafe_allow_html=True)
    st.progress(progress)
    st.caption(f"Estimated {latest['est_trips_remaining']} trips remaining to hit target.")

    # Simulated Footer
    st.markdown("<div class='uber-footer'><b>Uber</b> Engineering Hackathon 2026</div>", unsafe_allow_html=True)

def render_post_shift(fin_df, safe_df, goal, trips_df):
    """STATE B: Deep Analytics for pit stops."""
    st.markdown("### 📊 Post-Shift Analytics")
    
    col_chart, col_safety = st.columns([1.8, 1.2]) # Adjusted ratio for better fit

    with col_chart:
        st.markdown("#### Earnings Pace Chart")
        if not fin_df.empty and goal is not None and not trips_df.empty:
            
            # --- NEW: Merge Trip Details into Financial Data for Hover ---
            chart_data = pd.merge(fin_df, trips_df, on="trip_id", how="left")
            
            target_earnings = float(goal['target_earnings'])
            target_hours = float(goal['target_hours'])
            ideal_slope = target_earnings / target_hours
            chart_data['ideal_earnings'] = chart_data['elapsed_hours'] * ideal_slope
            
            # 1. Base Layer (Axes)
            base = alt.Chart(chart_data).encode(x=alt.X('elapsed_hours', title='Hours Driven'))
            
            # 2. Solid Blue Line (Actual Earnings)
            actual_line = base.mark_line(color='#276ef1', strokeWidth=3).encode(
                y=alt.Y('cumulative_earnings', title='Earnings ($)')
            )
            
            # 3. Dashed Gray Line (Target Pace)
            ideal_line = base.mark_line(color='gray', strokeDash=[5, 5], opacity=0.5).encode(
                y='ideal_earnings'
            )
            
            # 4. NEW: Interactive Hover Points!
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
            
            # Layer them all together
            st.altair_chart(actual_line + ideal_line + points, use_container_width=True)
            st.caption("Hover over the white dots to see specific trip details. Dashed line represents your target pace.")
        else:
            st.write("No financial data available.")

    with col_safety:
        st.markdown("#### Safety & Telemetry")
        
        # Calculate Safety Score
        score = 100
        if not safe_df.empty:
            highs = len(safe_df[safe_df['severity'] == 'high'])
            meds = len(safe_df[safe_df['severity'] == 'medium'])
            score = max(0, 100 - (highs * 10) - (meds * 5))
            
        color = "green" if score > 85 else "orange" if score > 70 else "red"
        st.markdown(f"**Overall Safety Score:** :{color}[{score}/100]")
        
        if not safe_df.empty:
            # --- NEW: Filtering System ---
            st.markdown("##### Filter Events")
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                sev_filter = st.multiselect("Severity", ["HIGH", "MEDIUM", "LOW"], default=["HIGH", "MEDIUM"])
            with f_col2:
                type_filter = st.multiselect("Event Type", ["Motion", "Audio", "Conflict"], default=["Motion", "Audio", "Conflict"])
            
            # Apply Filters
            filtered_df = safe_df[safe_df['severity'].str.upper().isin(sev_filter)]
            
            def match_type(context_str):
                context_str = str(context_str).lower()
                if "motion" in context_str and "audio" in context_str: return "Conflict"
                if "motion" in context_str: return "Motion"
                if "audio" in context_str: return "Audio"
                return "Other"
                
            filtered_df['event_category'] = filtered_df['context'].apply(match_type)
            filtered_df = filtered_df[filtered_df['event_category'].isin(type_filter)]
            
            # --- NEW: Scrollable Container ---
            st.markdown("##### Event Log")
            # This creates a fixed-height box with a native scrollbar!
            with st.container(height=350):
                if filtered_df.empty:
                    st.success("No events match your current filters.")
                else:
                    # Sort chronologically so it reads like a timeline
                    for idx, row in filtered_df.sort_values(by='timestamp').iterrows(): 
                        sev = row['severity'].upper()
                        icon = "🚨" if sev == "HIGH" else "⚠️" if sev == "MEDIUM" else "ℹ️"
                        
                        with st.expander(f"{icon} {sev} | {row['timestamp'].split(' ')[1]} | {row['trip_id']}"):
                            st.markdown(f"**Flag:** {row['flag_type'].replace('_', ' ').title()}")
                            st.markdown(f"**Details:** {row['explanation']}")
                            st.caption(f"Raw Context: {row['context']}")
        else:
            st.success("No critical safety events flagged today. Great driving!")

# ==========================================
# 4. MAIN EVENT LOOP (Real-Time Rendering)
# ==========================================
def main():
    with st.sidebar:
        st.markdown("### Control Panel")
        st.write("Welcome to the Uber Drive Pulse demo. Click below to start a fresh live simulation.")
        
        if st.button("Run Live Simulation", type="primary", use_container_width=True):
            # 1. Wipe the old files clean so the UI resets
            pd.DataFrame(columns=["log_id", "driver_id", "trip_id", "timestamp", "cumulative_earnings", "elapsed_hours", "trips_completed", "current_velocity", "required_velocity", "velocity_delta", "avg_earning_per_trip", "est_trips_remaining", "forecast_status"]).to_csv("data/earnings_velocity_log.csv", index=False)
            pd.DataFrame(columns=["flag_id", "trip_id", "driver_id", "timestamp", "elapsed_seconds", "flag_type", "severity", "explanation", "context"]).to_csv("data/flagged_moments.csv", index=False)
            
            # 2. Start the backend simulator in a background thread
            sim_thread = threading.Thread(target=run_simulator)
            sim_thread.start()
            
            st.success("Simulation started! Switch to the Live Shift tab.")
    # ---------------------------------

    fin_df, safe_df, goal, trips_df = load_data()
    
    tab_live, tab_analytics = st.tabs(["🚗 Live Shift", "📊 Pit Stop Analytics"])
    
    with tab_live:
        render_live_shift(fin_df, goal)
        
    with tab_analytics:
        render_post_shift(fin_df, safe_df, goal, trips_df)

    # Polling engine set to 0.5s for buttery smooth animations
    time.sleep(0.5)
    st.rerun()

if __name__ == "__main__":
    main()