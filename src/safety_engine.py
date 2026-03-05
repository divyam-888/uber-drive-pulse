import os
import math
import pandas as pd
import uuid
from datetime import datetime
from collections import deque

class SafetyEngine:
    def __init__(self):
        # --- System Configuration & Thresholds ---
        self.GRAVITY = 9.81
        self.HARSH_BRAKE_THRESHOLD = 4.0   
        self.DEVICE_DROP_THRESHOLD = 15.0  
        self.AUDIO_THRESHOLD_DB = 80.0     
        
        self.MOTION_WINDOW_SEC = 2.0
        self.AUDIO_WINDOW_SEC = 5.0
        self.COOLDOWN_SEC = 10             
        self.CONFLICT_BUFFER_SEC = 60      
        
        # --- Time-Based Memory Buffers ---
        # No maxlen; we store tuples of (datetime_obj, value)
        self.motion_buffer = deque()
        self.audio_buffer = deque()
        
        self.last_motion_alert_ts = None
        self.last_audio_alert_ts = None
        self.recent_alerts = deque(maxlen=20) 
        
        self.output_file = "data/flagged_moments.csv"
        self._initialize_output_file()

    def _initialize_output_file(self):
        """WIPES the old file on startup and creates fresh headers."""
        headers = ["flag_id", "trip_id", "driver_id", "timestamp", 
                   "elapsed_seconds", "flag_type", "severity", 
                   "explanation", "context"]
        # mode='w' forces an overwrite of old test runs
        pd.DataFrame(columns=headers).to_csv(self.output_file, mode='w', index=False)

    def _parse_time(self, ts_string):
        return datetime.strptime(ts_string, "%Y-%m-%d %H:%M:%S")

    def _maintain_time_window(self, buffer, current_ts, window_sec):
        """Pops old data out of the deque based on time, not row count."""
        while buffer and (current_ts - buffer[0][0]).total_seconds() > window_sec:
            buffer.popleft()

    def process_motion(self, row, driver_id):
        current_ts = self._parse_time(row['timestamp'])
        
        # Calculate 3D Linear Acceleration magnitude
        linear_accel = math.sqrt(row['accel_x']**2 + row['accel_y']**2 + (row['accel_z'] - self.GRAVITY)**2)
        
        self.motion_buffer.append((current_ts, linear_accel))
        self._maintain_time_window(self.motion_buffer, current_ts, self.MOTION_WINDOW_SEC)

        if len(self.motion_buffer) > 0:
            avg_accel = sum(val for ts, val in self.motion_buffer) / len(self.motion_buffer)
            
            # --- THE GPS DROP FIX ---
            speed = row.get('speed_kmh', None)
            # If speed is missing or NaN, assume they are driving (fail-safe)
            if pd.isna(speed) or speed is None:
                speed = 50.0
            
            # --- THE FIX: Check max instantaneous value, not average ---
            max_accel = max(val for ts, val in self.motion_buffer)
            if max_accel > self.DEVICE_DROP_THRESHOLD:
                self.motion_buffer.clear() # Phone dropped! Clear memory.
                return
                
            # Filter out door slams and phone tosses while parked
            if speed < 5.0 and avg_accel > self.HARSH_BRAKE_THRESHOLD:
                return 
                
            if avg_accel >= self.HARSH_BRAKE_THRESHOLD:
                if not self.last_motion_alert_ts or (current_ts - self.last_motion_alert_ts).total_seconds() >= self.COOLDOWN_SEC:
                    
                    self.last_motion_alert_ts = current_ts
                    self.recent_alerts.append((current_ts, 'motion'))
                    
                    # Dynamically scale severity based on BOTH force and speed
                    if avg_accel > 7.0 or (avg_accel > 5.0 and speed > 60.0):
                        sev = "high"
                    else:
                        sev = "medium"
                        
                    self._log_event(
                        trip_id=row['trip_id'],
                        driver_id=driver_id, # Use the passed-in ID!
                        timestamp=row['timestamp'],
                        elapsed_seconds=row['elapsed_seconds'],
                        flag_type="harsh_braking",
                        severity=sev,
                        explanation=f"Harsh brake ({avg_accel:.1f} m/s²) at {speed:.0f} km/h.",
                        context="Motion: harsh_brake"
                    )
                    self._check_for_conflict(row['trip_id'], driver_id, current_ts, row['elapsed_seconds'])

    # Do the same for audio to accept the driver_id
    def process_audio(self, row, driver_id):
        current_ts = self._parse_time(row['timestamp'])
        
        self.audio_buffer.append((current_ts, row['audio_level_db']))
        self._maintain_time_window(self.audio_buffer, current_ts, self.AUDIO_WINDOW_SEC)
        
        if len(self.audio_buffer) > 0:
            avg_audio = sum(val for ts, val in self.audio_buffer) / len(self.audio_buffer)
            
            if avg_audio >= self.AUDIO_THRESHOLD_DB:
                if not self.last_audio_alert_ts or (current_ts - self.last_audio_alert_ts).total_seconds() >= self.COOLDOWN_SEC:
                    
                    self.last_audio_alert_ts = current_ts
                    self.recent_alerts.append((current_ts, 'audio'))
                    
                    sev = "high" if avg_audio > 90.0 else "medium" if avg_audio > 85.0 else "low"
                    self._log_event(
                        trip_id=row['trip_id'],
                        driver_id=driver_id, # Use the passed-in ID!
                        timestamp=row['timestamp'],
                        elapsed_seconds=row['elapsed_seconds'],
                        flag_type="high_audio",
                        severity=sev,
                        explanation=f"Sustained elevated cabin noise ({avg_audio:.1f} dB avg).",
                        context="Audio: elevated"
                    )
                    self._check_for_conflict(row['trip_id'], driver_id, current_ts, row['elapsed_seconds'])

    def _check_for_conflict(self, trip_id, driver_id, current_ts, elapsed_seconds):
        has_recent_audio = False
        has_recent_motion = False
        
        for alert_ts, alert_type in list(self.recent_alerts):
            if (current_ts - alert_ts).total_seconds() <= self.CONFLICT_BUFFER_SEC:
                if alert_type == 'audio': has_recent_audio = True
                if alert_type == 'motion': has_recent_motion = True
                
        if has_recent_audio and has_recent_motion:
            self.recent_alerts.clear()
            self._log_event(
                trip_id=trip_id,
                driver_id=driver_id,
                timestamp=current_ts.strftime("%Y-%m-%d %H:%M:%S"),
                elapsed_seconds=elapsed_seconds,
                flag_type="conflict_moment",
                severity="high",
                explanation=f"Combined signal: Harsh braking + sustained high audio within {self.CONFLICT_BUFFER_SEC}s.",
                context="Motion: harsh_brake | Audio: argument"
            )

    def _log_event(self, trip_id, driver_id, timestamp, elapsed_seconds, flag_type, severity, explanation, context):
        flag_id = f"FLAG_{uuid.uuid4().hex[:8].upper()}"
        new_row = pd.DataFrame([{
            "flag_id": flag_id, "trip_id": trip_id, "driver_id": driver_id, 
            "timestamp": timestamp, "elapsed_seconds": elapsed_seconds, 
            "flag_type": flag_type, "severity": severity, 
            "explanation": explanation, "context": context
        }])
        new_row.to_csv(self.output_file, mode='a', header=False, index=False)
        print(f"🚨 [SAFETY ENGINE] {severity.upper()} ALERT: {flag_type} at {timestamp}")

