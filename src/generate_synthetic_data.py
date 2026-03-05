import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def generate_data():
    # 1. Setup Data Directory
    os.makedirs('data', exist_ok=True)
    
    # Base configuration
    driver_id = "DRV_ALEX"
    date_str = "2024-10-25"
    shift_start = datetime.strptime(f"{date_str} 08:00:00", "%Y-%m-%d %H:%M:%S")
    
    # --- 1. Generate Driver & Goals (For Person 2) ---
    drivers_df = pd.DataFrame([{
        "driver_id": driver_id, "name": "Alex Kumar", "city": "Mumbai", 
        "shift_preference": "morning", "avg_hours_per_day": 8.0, 
        "avg_earnings_per_hour": 180, "experience_months": 24, "rating": 4.9
    }])
    
    goals_df = pd.DataFrame([{
        "goal_id": "GOAL001", "driver_id": driver_id, "date": date_str,
        "shift_start_time": "08:00:00", "shift_end_time": "16:00:00",
        "target_earnings": 1500, "target_hours": 8, "current_earnings": 0,
        "current_hours": 0, "status": "in_progress", "earnings_velocity": 0, "goal_completion_forecast": "pending"
    }])

    # --- 2. Generate Trips (Synchronous anchor for Person 1 & 2) ---
    trips_data = []
    current_time = shift_start + timedelta(minutes=15) # First trip starts at 8:15
    
    # Define the 4 test cases
    trip_configs = [
        {"duration_min": 15, "fare": 120, "distance": 5.2, "anomaly": "none"},
        {"duration_min": 22, "fare": 210, "distance": 8.5, "anomaly": "hard_brake"},
        {"duration_min": 18, "fare": 160, "distance": 6.1, "anomaly": "loud_noise"},
        {"duration_min": 25, "fare": 250, "distance": 11.0, "anomaly": "conflict"}
    ]

    accel_data_list = []
    audio_data_list = []

    for i, config in enumerate(trip_configs):
        trip_id = f"TRIP_{i+1:03d}"
        end_time = current_time + timedelta(minutes=config["duration_min"])
        
        # Add to Trips
        trips_data.append({
            "trip_id": trip_id, "driver_id": driver_id, "date": date_str,
            "start_time": current_time.strftime("%H:%M:%S"),
            "end_time": end_time.strftime("%H:%M:%S"),
            "duration_min": config["duration_min"], "distance_km": config["distance"],
            "fare": config["fare"], "surge_multiplier": 1.0, 
            "pickup_location": f"Location A{i}", "dropoff_location": f"Location B{i}",
            "trip_status": "completed"
        })

        # --- 3. Generate High-Frequency Sensor Data (For Person 1) ---
        # Generate 1 row per second
        timestamps = pd.date_range(start=current_time, end=end_time, freq='s')
        elapsed_secs = np.arange(len(timestamps))
        
        # Base normal data (gravity on Z, quiet cabin)
        z_accel = np.random.normal(9.8, 0.2, len(timestamps))
        y_accel = np.random.normal(0, 0.5, len(timestamps)) # forward/back motion
        audio_db = np.random.normal(55, 3, len(timestamps)) # normal road noise
        
        # INJECT ANOMALIES based on config
        midpoint = len(timestamps) // 2
        
        if config["anomaly"] in ["hard_brake", "conflict"]:
            # Inject a massive 3-second deceleration spike in the Y axis
            y_accel[midpoint:midpoint+3] = np.random.normal(-8.0, 1.0, 3) 
            
        if config["anomaly"] in ["loud_noise", "conflict"]:
            # Inject 15 seconds of shouting (85-95 dB) right after the midpoint
            audio_db[midpoint+1:midpoint+16] = np.random.normal(90, 2, 15)

        # Build DataFrames for this trip
        for j in range(len(timestamps)):
            accel_data_list.append({
                "sensor_id": f"ACC_{trip_id}_{j}", "trip_id": trip_id,
                "timestamp": timestamps[j].strftime("%Y-%m-%d %H:%M:%S"),
                "elapsed_seconds": elapsed_secs[j],
                "accel_x": np.random.normal(0, 0.2), "accel_y": y_accel[j], "accel_z": z_accel[j],
                "speed_kmh": 40 + np.random.normal(0, 5), "gps_lat": 19.0 + (j*0.0001), "gps_lon": 72.8 + (j*0.0001)
            })
            
            # Simple classification logic for the raw data
            classification = "loud" if audio_db[j] > 80 else "normal"
            
            audio_data_list.append({
                "audio_id": f"AUD_{trip_id}_{j}", "trip_id": trip_id,
                "timestamp": timestamps[j].strftime("%Y-%m-%d %H:%M:%S"),
                "elapsed_seconds": elapsed_secs[j],
                "audio_level_db": round(audio_db[j], 1),
                "audio_classification": classification,
                "sustained_duration_sec": 0 # Your logic will calculate this later!
            })

        # Advance time for the next trip (driver takes a 10 min break)
        current_time = end_time + timedelta(minutes=10)

    # --- 4. Save Everything to CSV ---
    drivers_df.to_csv("data/drivers.csv", index=False)
    goals_df.to_csv("data/driver_goals.csv", index=False)
    pd.DataFrame(trips_data).to_csv("data/trips.csv", index=False)
    pd.DataFrame(accel_data_list).to_csv("data/accelerometer_data.csv", index=False)
    pd.DataFrame(audio_data_list).to_csv("data/audio_intensity_data.csv", index=False)
    
    print("Successfully generated massive synthetic dataset in the /data folder!")
    print(f"Generated {len(accel_data_list)} rows of sensor data across {len(trip_configs)} trips.")

if __name__ == "__main__":
    generate_data()