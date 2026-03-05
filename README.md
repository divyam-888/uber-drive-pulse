# Uber Drive Pulse

Uber Drive Pulse is a **real-time driver telemetry and financial analytics system** designed for gig-economy drivers.  
Built for the **Uber Engineering Hackathon 2026**, the system processes high-frequency sensor streams and trip data to provide:

- Live shift financial pacing
- Real-time safety monitoring
- Post-shift behavioral analytics

The system simulates a **production-style event streaming architecture** where sensor signals and trip completions are processed in chronological order and written to structured logs that power a live dashboard.

---

# Demo Overview

Uber Drive Pulse answers two key questions for drivers:

### 1. Am I driving safely?
Using accelerometer and audio telemetry, the system detects:

- Harsh braking
- Cabin noise spikes
- Device drops
- Passenger conflict situations

### 2. Am I on track to hit my earnings goal?
The financial engine calculates:

- Current earnings velocity
- Target pacing
- Remaining trips required
- Forecast status (Ahead / On Track / Behind / Achieved)

The dashboard shows this information in a **minimal distraction Live Shift interface**, with deeper insights available after the shift ends.

---

# System Architecture

The platform is designed as a **modular event-driven pipeline**.

```
Synthetic Data Generator
        │
        ▼
Sensor CSV Streams (Accelerometer + Audio)
        │
        ▼
Simulator Event Loop
        │
        ├── Safety Engine
        │       │
        │       ▼
        │  flagged_moments.csv
        │
        └── Financial Engine
                │
                ▼
        earnings_velocity_log.csv
                │
                ▼
        Streamlit Dashboard
```

### Key Design Principles

- **Event-driven simulation**
- **Deterministic heuristics instead of heavy ML**
- **Chronological sensor replay**
- **Decoupled backend and frontend**
- **Live polling UI**

---

# Core Features

## Real-Time Safety Engine

Processes high-frequency telemetry streams to detect dangerous situations.

### Motion Analysis
Uses accelerometer signals to detect:

- Harsh braking
- Phone/device drops
- Rapid braking sequences

Features:

- 3D linear acceleration calculation
- Sliding time windows using `deque`
- Speed-aware filtering to prevent false positives

### Audio Analysis
Detects abnormal cabin audio levels:

- Loud music
- Passenger arguments
- Sustained noise spikes

Audio signals are averaged across a time window to identify abnormal conditions.

### Conflict Detection

The system correlates motion and audio events.

Example:

```
Harsh braking
+
Sustained high audio
=
Passenger conflict event
```

These compound signals trigger a **high-severity safety alert**.

---

## Financial Velocity Engine

Tracks a driver's earnings performance during a shift.

Metrics include:

- Cumulative earnings
- Earnings velocity ($/hour)
- Forecast pacing relative to target goal
- Remaining trips required

Forecast statuses:

| Status | Meaning |
|------|------|
| AHEAD | Driver exceeds target pace |
| ON_TRACK | Driver is near target pace |
| BEHIND | Driver must increase pace |
| ACHIEVED | Earnings goal reached |

---

## Live Driver Dashboard

Built with **Streamlit** and **Altair**.

Two main interfaces:

### 🚗 Live Shift View

Minimal distraction interface showing:

- Current earnings
- Earnings velocity
- Forecast status
- Goal progress bar

---

### 📊 Pit Stop Analytics

Post-shift interactive analysis including:

- Earnings vs ideal trajectory chart
- Trip-by-trip financial breakdown
- Safety event log
- Safety score calculation
- Filterable event explorer

---

# Directory Structure

```
uber-drive-pulse/
│
├── data/
│   ├── accelerometer_data.csv
│   ├── audio_intensity_data.csv
│   ├── drivers.csv
│   ├── driver_goals.csv
│   ├── trips.csv
│   ├── flagged_moments.csv
│   └── earnings_velocity_log.csv
│
├── src/
│   ├── app.py
│   ├── simulator.py
│   ├── generate_synthetic_data.py
│   ├── safety_engine.py
│   └── financial_engine.py
│
├── requirements.txt
└── README.md
```

---

# Synthetic Dataset Generation

The repository includes a **data generator that creates a realistic driving shift simulation**.

### Generated Components

- Driver profile
- Driver earnings goal
- 9 trip events
- Per-second accelerometer stream
- Per-second audio stream

Each trip includes **specific injected anomalies** to test detection logic.

Example anomalies:

| Event | Description |
|------|------|
Door Slam | Acceleration spike while parked |
High Speed Brake | Sudden braking at highway speed |
Loud Radio | Sustained elevated audio |
Tunnel Brake | GPS dropout during braking |
Passenger Conflict | High audio + harsh braking |
Rapid Brakes | Multiple braking spikes |
Device Drop | Large accelerometer spike |

This enables deterministic testing of the telemetry engine.

---

# Safety Engine Logic

The safety engine processes motion and audio signals using **time-window buffers**.

Example motion logic:

```
linear_accel = sqrt(ax² + ay² + (az - g)²)

if avg_accel > threshold:
    log harsh braking event
```

The engine uses:

- Sliding windows
- Cooldown timers
- Multi-signal correlation
- GPS-aware filtering

Alerts are written to:

```
data/flagged_moments.csv
```

---

# Simulator Event Loop

The simulator replays sensor streams chronologically.

Key steps:

1. Load synthetic datasets
2. Merge audio and motion streams
3. Sort by timestamp
4. Dispatch each event to the correct engine

```
Motion events → Safety Engine
Audio events → Safety Engine
Trip completion → Financial Engine
```

This design mimics a **real-time streaming pipeline**.

---

# Installation

## Requirements

- Python 3.8+
- pip

---

## Clone the repository

```bash
git clone https://github.com/divyam-888/uber-drive-pulse.git
cd uber-drive-pulse
```

---

## Create virtual environment

Mac / Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

---

## Install dependencies

```bash
pip install -r requirements.txt
```

---

# Running the Application

The system runs entirely from the Streamlit dashboard.

Start the app:

```bash
streamlit run src/app.py
```

When the dashboard opens:

1. Click **"Initialize System & Start Shift"**
2. Synthetic data will be generated
3. The simulator begins streaming events
4. The dashboard updates in real time

---

# Example Data Contracts

### Accelerometer Input

```json
{
  "timestamp": "2024-10-25 08:15:00",
  "accel_x": 0.2,
  "accel_y": -7.5,
  "accel_z": 9.8,
  "speed_kmh": 65
}
```

---

### Safety Event Output

```
flag_id,trip_id,timestamp,flag_type,severity,explanation
FLAG_A1B2C3D4,TRIP_004,2024-10-25 11:25:02,conflict_moment,HIGH,Combined signal: Harsh braking + sustained high audio within 60s
```

---

### Financial Log Output

```
log_id,trip_id,timestamp,cumulative_earnings,current_velocity,forecast_status
VEL_E5F6G7H8,TRIP_004,2024-10-25 11:00:00,850.00,283.33,AHEAD
```

---

# Technology Stack

Backend

- Python
- Pandas
- NumPy

Streaming Simulation

- Event loop architecture
- Chronological sensor replay

Frontend

- Streamlit
- Altair charts

Data Storage

- CSV log files

---

# Why Deterministic Rules Instead of Machine Learning?

For hackathon prototyping and real-time edge environments:

Advantages:

- Predictable behavior
- Fast execution
- No training pipeline
- Fully explainable outputs

This makes the system easier to deploy on **mobile edge devices** in future versions.

---

# Future Improvements

Possible next steps:

### Real Sensor Integration
- Mobile accelerometer APIs
- In-vehicle telematics
- Smartphone microphone input

### Streaming Infrastructure
Replace CSV logs with:

- Kafka
- Redis streams
- WebSocket feeds

### ML Behavioral Models
Train models to detect:

- Driver fatigue
- Aggressive driving patterns
- Passenger dispute prediction

### Fleet Dashboard
Allow Uber fleet managers to monitor:

- Driver safety scores
- Real-time operational metrics

---

# Hackathon Context

This project was built for:

**Uber Engineering Hackathon 2026**

Goal: explore how **real-time telemetry and financial analytics** could improve the experience and safety of gig-economy drivers.

---

# Author

**Divyam Nagpal**

Mathematics & Computing  
IIT (BHU) Varanasi

GitHub:  
https://github.com/divyam-888

---

# License

MIT License
