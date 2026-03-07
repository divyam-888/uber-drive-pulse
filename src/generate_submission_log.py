import pandas as pd
import re
import os

def generate_uber_submission_log():
    print("Processing Uber Compliance Log...")
    output_rows = []
    
    # --- 1. Process Safety Events (flagged_moments.csv) ---
    try:
        safety_df = pd.read_csv("data/flagged_moments.csv")
        for _, row in safety_df.iterrows():
            flag_type = str(row['flag_type']).lower()
            explanation = str(row['explanation'])
            
            # Defaults
            signal_type = "UNKNOWN"
            raw_val = "N/A"
            threshold = "N/A"
            
            # Robust extraction based on flag type
            if "brake" in flag_type or "braking" in flag_type:
                signal_type = "ACCELEROMETER"
                threshold = 4.0
                match = re.search(r'([\d.]+)\s*m/s²', explanation)
                if match:
                    raw_val = float(match.group(1))
            
            elif "audio" in flag_type:
                signal_type = "AUDIO"
                threshold = 80.0
                match = re.search(r'([\d.]+)\s*dB', explanation)
                if match:
                    raw_val = float(match.group(1))
            
            elif "conflict" in flag_type:
                signal_type = "MULTIMODAL"
                threshold = "COMPOSITE"
                raw_val = "COMBINED_SPIKE"

            output_rows.append({
                "timestamp": row['timestamp'],
                "signal_type": signal_type,
                "raw_value": raw_val,
                "threshold": threshold,
                "event_label": flag_type, # e.g., harsh_braking, high_audio, conflict_moment
                "context": explanation    # Uses the exact explanation from the safety log
            })
    except FileNotFoundError:
        print("Warning: data/flagged_moments.csv not found.")

    # --- 2. Process Financial Events (earnings_velocity_log.csv) ---
    try:
        finance_df = pd.read_csv("data/earnings_velocity_log.csv")
        for _, row in finance_df.iterrows():
            # Format the context string exactly as requested
            curr_vel = row['current_velocity']
            req_vel = row['required_velocity']
            delta = row['velocity_delta']
            context_str = f"Required Velocity: ${req_vel:.2f}/hr | Current Velocity: ${curr_vel:.2f}/hr | Delta: ${delta:.2f}/hr"
            
            output_rows.append({
                "timestamp": row['timestamp'],
                "signal_type": "EARNINGS",
                "raw_value": curr_vel,
                "threshold": req_vel,
                "event_label": str(row['forecast_status']).lower(), # e.g., behind, on_track, ahead, achieved
                "context": context_str
            })
    except FileNotFoundError:
        print("Warning: data/earnings_velocity_log.csv not found.")

    # --- 3. Compile and Export ---
    if output_rows:
        final_df = pd.DataFrame(output_rows)
        
        # Ensure strict column ordering
        final_df = final_df[["timestamp", "signal_type", "raw_value", "threshold", "event_label", "context"]]
        
        # Sort chronologically
        final_df = final_df.sort_values(by="timestamp")
        
        output_path = "data/uber_processed_output.csv"
        final_df.to_csv(output_path, index=False)
        print(f"Success! Final submission log generated at: {output_path}")
    else:
        print("Error: No data found to process. Please run the simulator first.")

if __name__ == "__main__":
    generate_uber_submission_log()