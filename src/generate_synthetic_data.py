import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def generate_data():
    os.makedirs('data', exist_ok=True)
    
    driver_id = "DRV_ALEX"
    date_str = "2024-10-25"
    shift_start = datetime.strptime(f"{date_str} 08:00:00", "%Y-%m-%d %H:%M:%S")
    
    # Driver & Goals 
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

    # The 9-Trip Test Cases
    trips_data = []
    current_time = shift_start + timedelta(minutes=15) 
    
    trip_configs = [
        # start slow. 15 mins for $20 (Pace: $80/hr -> BEHIND)
        {"dur": 15, "fare": 20, "dist": 3.0, "anomaly": "door_slam"},        
        # stuck in traffic. 45 mins for $50 (Pace drops -> BEHIND)
        {"dur": 45, "fare": 50, "dist": 8.0, "anomaly": "high_speed_brake"}, 
        # still struggling. 50 mins for $60 (Pace -> BEHIND)
        {"dur": 50, "fare": 60, "dist": 10.0, "anomaly": "loud_radio"},      
        # starting to catch up
        {"dur": 25, "fare": 150, "dist": 12.0, "anomaly": "gps_drop_brake"}, 
        # audio spike 
        {"dur": 30, "fare": 180, "dist": 15.0, "anomaly": "conflict"},        
        # stop & go traffic 
        {"dur": 20, "fare": 90, "dist": 6.0, "anomaly": "rapid_brakes"},     
        # phone drop
        {"dur": 15, "fare": 80, "dist": 8.0, "anomaly": "device_drop"},      
        # surge, catching up completely
        {"dur": 40, "fare": 650, "dist": 45.0, "anomaly": "none"},            
        # final trip to hit the $1500 goal
        {"dur": 50, "fare": 250, "dist": 20.0, "anomaly": "none"}              
    ]

    accel_data_list = []
    audio_data_list = []

    for i, config in enumerate(trip_configs):
        trip_id = f"TRIP_{i+1:03d}"
        end_time = current_time + timedelta(minutes=config["dur"])
        
        trips_data.append({
            "trip_id": trip_id, "driver_id": driver_id, "date": date_str,
            "start_time": current_time.strftime("%H:%M:%S"),
            "end_time": end_time.strftime("%H:%M:%S"),
            "duration_min": config["dur"], "distance_km": config["dist"],
            "fare": config["fare"], "surge_multiplier": 1.0, 
            "pickup_location": f"Zone {i}A", "dropoff_location": f"Zone {i}B",
            "trip_status": "completed"
        })

        timestamps = pd.date_range(start=current_time, end=end_time, freq='s')
        elapsed_secs = np.arange(len(timestamps))
        
        z_accel = np.random.normal(9.8, 0.2, len(timestamps))
        y_accel = np.random.normal(0, 0.5, len(timestamps)) 
        audio_db = np.random.normal(55, 3, len(timestamps)) 
        speed_kmh = np.random.normal(40, 5, len(timestamps))
        
        mid = len(timestamps) // 2
        
        if config["anomaly"] == "door_slam":
            speed_kmh[10:15] = 0.0 # Car is parked
            y_accel[10:12] = -7.0  # Big jolt
            
        elif config["anomaly"] == "high_speed_brake":
            speed_kmh[mid:mid+3] = 75.0 # Highway speeds
            y_accel[mid:mid+3] = -6.5   # Moderate brake, but dangerous at high speed
            
        elif config["anomaly"] == "loud_radio":
            audio_db[mid:mid+10] = 82.0 # Sustained 82dB (Low severity)
            
        elif config["anomaly"] == "gps_drop_brake":
            speed_kmh[mid:mid+5] = np.nan # GPS drops out in tunnel
            y_accel[mid+1:mid+4] = -7.5   # Hard brake in tunnel
            
        elif config["anomaly"] == "conflict":
            y_accel[mid:mid+3] = -8.5     # Hard brake
            audio_db[mid-2:mid+12] = 93.0 # Shouting (High severity audio)
            
        elif config["anomaly"] == "rapid_brakes":
            y_accel[mid:mid+2] = -7.0     # Brake 1
            y_accel[mid+6:mid+8] = -7.5   # Brake 2 (Just 6 seconds later)
            
        elif config["anomaly"] == "device_drop":
            y_accel[mid:mid+2] = -18.0    # Massive >15m/s2 spike

        for j in range(len(timestamps)):
            accel_data_list.append({
                "sensor_id": f"ACC_{trip_id}_{j}", "trip_id": trip_id,
                "timestamp": timestamps[j].strftime("%Y-%m-%d %H:%M:%S"),
                "elapsed_seconds": elapsed_secs[j],
                "accel_x": np.random.normal(0, 0.2), "accel_y": y_accel[j], "accel_z": z_accel[j],
                "speed_kmh": speed_kmh[j], "gps_lat": 19.0 + (j*0.0001), "gps_lon": 72.8 + (j*0.0001)
            })
            
            classification = "loud" if audio_db[j] > 80 else "normal"
            audio_data_list.append({
                "audio_id": f"AUD_{trip_id}_{j}", "trip_id": trip_id,
                "timestamp": timestamps[j].strftime("%Y-%m-%d %H:%M:%S"),
                "elapsed_seconds": elapsed_secs[j],
                "audio_level_db": round(audio_db[j], 1),
                "audio_classification": classification,
                "sustained_duration_sec": 0 
            })

        # driver takes a 10 min break between trips
        current_time = end_time + timedelta(minutes=10)

    drivers_df.to_csv("data/drivers.csv", index=False)
    goals_df.to_csv("data/driver_goals.csv", index=False)
    pd.DataFrame(trips_data).to_csv("data/trips.csv", index=False)
    pd.DataFrame(accel_data_list).to_csv("data/accelerometer_data.csv", index=False)
    pd.DataFrame(audio_data_list).to_csv("data/audio_intensity_data.csv", index=False)
    
    print("✅ Successfully generated the 9-Trip Edge-Case Dataset!")

if __name__ == "__main__":
    generate_data()