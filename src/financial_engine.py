import os
import math
import uuid
import pandas as pd
from datetime import datetime

class FinancialEngine:
    def __init__(self):
        # The Ledger: Stores running state for each driver
        # Structure: {'DRV_ALEX': {'earnings': 120, 'trips': 1, 'start_time': dt}}
        self.ledgers = {}
        
        # Load the shift goals into memory
        self.goals_df = pd.read_csv("data/driver_goals.csv")
        
        self.output_log = "data/earnings_velocity_log.csv"
        self._initialize_output_file()

    def _initialize_output_file(self):
        """Wipes old test data and sets up the upgraded Data Contract."""
        headers = ["log_id", "driver_id", "trip_id", "timestamp", 
                   "cumulative_earnings", "elapsed_hours", "trips_completed",
                   "current_velocity", "required_velocity", "velocity_delta",
                   "avg_earning_per_trip", "est_trips_remaining", "forecast_status"]
        pd.DataFrame(columns=headers).to_csv(self.output_log, mode='w', index=False)

    def _parse_time(self, ts_string):
        return datetime.strptime(ts_string, "%Y-%m-%d %H:%M:%S")

    def _get_goal_for_driver(self, driver_id):
        """Fetches the shift constraints for the driver."""
        goal_row = self.goals_df[self.goals_df['driver_id'] == driver_id]
        if goal_row.empty:
            return None
        return goal_row.iloc[0]

    def _initialize_ledger(self, driver_id, goal):
        """Sets up the driver's running totals on their first trip."""
        if driver_id not in self.ledgers:
            # Combine the date and shift_start_time from the goals CSV
            start_str = f"{goal['date']} {goal['shift_start_time']}"
            end_str = f"{goal['date']} {goal['shift_end_time']}"

            # --- THE MIDNIGHT SHIFT FIX ---
            if end_str <= start_str:
                end_str += timedelta(days=1)
            
            self.ledgers[driver_id] = {
                "start_time": self._parse_time(start_str),
                "end_time": self._parse_time(end_str),
                "cumulative_earnings": 0.0,
                "trips_completed": 0,
                "target_earnings": float(goal['target_earnings'])
            }

    def process_completed_trip(self, trip_row, current_time_dt):
        """Called by simulator.py every time a trip finishes."""
        driver_id = trip_row['driver_id']
        fare = float(trip_row['fare'])
        trip_id = trip_row['trip_id']
        
        goal = self._get_goal_for_driver(driver_id)
        if goal is None:
            return # Skip if driver has no set goals
            
        self._initialize_ledger(driver_id, goal)
        ledger = self.ledgers[driver_id]
        
        # 1. Update Core State
        ledger['cumulative_earnings'] += fare
        ledger['trips_completed'] += 1
        
        # 2. Time Calculations
        elapsed_delta = current_time_dt - ledger['start_time']
        elapsed_hours = elapsed_delta.total_seconds() / 3600.0
        
        total_shift_hours = (ledger['end_time'] - ledger['start_time']).total_seconds() / 3600.0
        remaining_hours = total_shift_hours - elapsed_hours
        
        # 3. New Functionalities (Averages & Trip Projections)
        avg_earning_per_trip = ledger['cumulative_earnings'] / ledger['trips_completed']
        
        remaining_target = max(0, ledger['target_earnings'] - ledger['cumulative_earnings'])
        est_trips_remaining = math.ceil(remaining_target / avg_earning_per_trip) if avg_earning_per_trip > 0 else 0

        # 4. Velocity Calculations & Edge Cases
        # Edge Case A: Warm-up period (Prevent infinite velocity if 1st trip ends in 5 mins)
        safe_elapsed = max(elapsed_hours, 0.5) 
        current_velocity = ledger['cumulative_earnings'] / safe_elapsed
        
        # Edge Case B: Overtime / Shift Ended
        safe_remaining = max(remaining_hours, 0.01)
        required_velocity = remaining_target / safe_remaining
        
        # Edge Case C: Goal Achieved
        if ledger['cumulative_earnings'] >= ledger['target_earnings']:
            required_velocity = 0.0
            est_trips_remaining = 0
            forecast_status = "achieved"
        else:
            forecast_ratio = (ledger['cumulative_earnings'] + (current_velocity * remaining_hours)) / ledger['target_earnings']
            if forecast_ratio > 1.05:
                forecast_status = "ahead"
            elif forecast_ratio < 0.90:
                forecast_status = "behind"
            else:
                forecast_status = "on_track"

        velocity_delta = current_velocity - required_velocity

        # 5. Log the Output (The Data Contract for Person 3)
        self._log_financial_event(
            driver_id, trip_id, current_time_dt.strftime("%Y-%m-%d %H:%M:%S"),
            ledger['cumulative_earnings'], elapsed_hours, ledger['trips_completed'],
            current_velocity, required_velocity, velocity_delta, 
            avg_earning_per_trip, est_trips_remaining, forecast_status
        )

    def _log_financial_event(self, driver_id, trip_id, timestamp, cumulative_earnings, 
                             elapsed_hours, trips_completed, current_velocity, 
                             required_velocity, velocity_delta, avg_earning_per_trip, 
                             est_trips_remaining, forecast_status):
                             
        log_id = f"VEL_{uuid.uuid4().hex[:8].upper()}"
        
        new_row = pd.DataFrame([{
            "log_id": log_id, "driver_id": driver_id, "trip_id": trip_id, 
            "timestamp": timestamp, "cumulative_earnings": round(cumulative_earnings, 2), 
            "elapsed_hours": round(elapsed_hours, 2), "trips_completed": trips_completed,
            "current_velocity": round(current_velocity, 2), "required_velocity": round(required_velocity, 2), 
            "velocity_delta": round(velocity_delta, 2), "avg_earning_per_trip": round(avg_earning_per_trip, 2), 
            "est_trips_remaining": est_trips_remaining, "forecast_status": forecast_status
        }])
        
        new_row.to_csv(self.output_log, mode='a', header=False, index=False)
        
        # Print a clean summary to terminal
        print(f"💰 [FINANCE] {trip_id} Logged. Earned: ${cumulative_earnings:.0f}/{self.ledgers[driver_id]['target_earnings']:.0f} | Pace: ${current_velocity:.0f}/hr | Remaining Trips ~{est_trips_remaining} | Status: {forecast_status.upper()}")