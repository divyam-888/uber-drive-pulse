import pandas as pd
import time
from datetime import datetime

from financial_engine import FinancialEngine
from safety_engine import SafetyEngine

def run_simulator():
    print("🚦 Initializing Uber Drive Pulse Simulator...")
    safety_engine = SafetyEngine()
    financial_engine = FinancialEngine()
    
    accel_df = pd.read_csv("data/accelerometer_data.csv")
    audio_df = pd.read_csv("data/audio_intensity_data.csv")
    trips_df = pd.read_csv("data/trips.csv")
    
    # tag the data based on event type
    accel_df['event_type'] = 'motion'
    audio_df['event_type'] = 'audio'
    
    # combine and sort both audio and motion data strictly by exact timestamp
    print("🔄 Merging sensor streams chronologically...")
    stream_df = pd.concat([accel_df, audio_df]).sort_values(by='timestamp')
    
    # convert trip end times to easily check when a trip finishes
    trips_df['end_time_dt'] = pd.to_datetime(trips_df['date'] + ' ' + trips_df['end_time'])
    print("🔗 Building Trip-to-Driver relational map...")
    trip_to_driver = dict(zip(trips_df['trip_id'], trips_df['driver_id']))

    completed_trips_tracked = set()

    print("🚀 Starting Live Stream Simulation...\n")
    print("-" * 50)
    
    # the event loop simulating the passage of time, by sending data of each second (here we speed it up send 1 second data in 0.005 seconds)
    # the event loop (Optimized with itertuples for 50x speed)
    for row in stream_df.itertuples():
        current_time_str = row.timestamp
        current_time_dt = pd.to_datetime(current_time_str)
        event_type = row.event_type
        trip_id = row.trip_id
        driver_id = trip_to_driver.get(trip_id, 'UNKNOWN')
        
        # covert itertuple object to a dictionary 
        row_dict = row._asdict()
        
        # check this event for motion and audio flags
        if event_type == 'motion':
            safety_engine.process_motion(row_dict, driver_id) 
        elif event_type == 'audio':
            safety_engine.process_audio(row_dict, driver_id)
            
        # check if the current trip just ended
        trip_info = trips_df[trips_df['trip_id'] == trip_id].iloc[0]
        if current_time_dt >= trip_info['end_time_dt'] and trip_id not in completed_trips_tracked:
            print(f"\n💰 [EVENT] {trip_id} Completed at {current_time_str}!")
            print(f"💰 Dispatching Fare: ${trip_info['fare']} to Financial Engine...\n")
            
            financial_engine.process_completed_trip(trip_info, current_time_dt)
            
            completed_trips_tracked.add(trip_id)
            print("-" * 50)

        # pause to simulate real-time (set to 0.01 for fast testing, 1.0 for real-time demo)
        time.sleep(0.002)

if __name__ == "__main__":
    run_simulator()
