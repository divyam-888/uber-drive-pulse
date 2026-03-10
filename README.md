# Uber Drive Pulse
### Engineering Handoff README  
Uber Engineering Hackathon 2026

---

# Project Overview

Uber Drive Pulse is a **real-time telemetry and financial analytics prototype** designed to simulate how driver safety signals and earnings performance could be monitored during a shift.

The system ingests **high-frequency accelerometer and audio sensor streams**, processes them through deterministic safety heuristics, tracks **driver earnings velocity**, and surfaces the results in a **live Streamlit dashboard**.

The project was designed to demonstrate how Uber could combine:

- onboard telemetry
- behavioral safety detection
- earnings pacing analytics

into a **single real-time driver assistance interface**.

---

# Github Link

URL:

```
https://github.com/divyam-888/uber-drive-pulse
```

---

# Live Deployment Link

Streamlit Cloud URL:

```
https://uber-drive-pulse.streamlit.app/
```

If running locally for judging, follow the setup instructions below.

---

# Demo Video

A short walkthrough demonstrating the full pipeline and dashboard.

```
https://drive.google.com/file/d/1byk1YipIwYIa_ph_FmS6JRM3_fNPakZ2/view?usp=sharing
```

---


# Setup Instruction

## 1. Clone the repository

```
git clone https://github.com/divyam-888/uber-drive-pulse.git
cd uber-drive-pulse
```

---

## 2. Create virtual environment

Mac / Linux

```
python3 -m venv venv
source venv/bin/activate
```

Windows

```
python -m venv venv
venv\Scripts\activate
```

---

## 3. Install dependencies

```
pip install -r requirements.txt
```

---

# Running the Application

This is an event-driven system. To view the full live pipeline locally, you must utilize two separate terminal windows to run the frontend and backend simultaneously.

---

## 1. Initialize Data and Frontend

In your first terminal, generate the synthetic test data and start the user interface.

```bash
python src/generate_synthetic_data.py
streamlit run src/app.py
```

Your browser will automatically open the dashboard.

Leave the UI on the **"Live Shift"** tab. The dashboard will initially display a **waiting state** until the simulator begins emitting events.

**Important behavior**

The dashboard reads previously generated logs from the `data/` directory.  
If the following files are already present:

```
data/flagged_moments.csv
data/earnings_velocity_log.csv
```

the dashboard will immediately load and display the existing run’s data instead of showing the waiting state.

These files are included in the repository to satisfy the hackathon submission requirement of providing output artifacts.

If you want to run a **fresh simulation**, ensure these files are removed before starting the application.

Example:

```bash
rm data/flagged_moments.csv
rm data/earnings_velocity_log.csv
```

Then rerun Step 1 to start with a clean dataset.

---

## 2. Trigger the Backend Simulator

Open a second terminal window, activate your virtual environment, and execute the event loop.

```bash
python src/simulator.py
```
As the backend processes the simulated trips in the terminal, the Streamlit dashboard in your browser will automatically poll the new data and animate the progress bars and charts in real-time.

---

This will:

1. generate synthetic data
2. start the simulator
3. stream events to the dashboard

---

## 6. Generate submission output

After the simulation finishes, run:

```
python src/generate_uber_submission_log.py
```

This produces:

```
data/uber_processed_output.csv
```

---

# System Architecture

The system simulates a **real-time event processing pipeline**.

```
Synthetic Data Generator
        │
        ▼
Sensor Streams (Accelerometer + Audio)
        │
        ▼
Chronological Event Simulator
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
Submission Log Generator
                │
                ▼
uber_processed_output.csv
                │
                ▼
Streamlit Dashboard
```

The system is intentionally **modular** so each component can evolve independently.

---

# Repository Structure

```
uber-drive-pulse/

data/
    accelerometer_data.csv
    audio_intensity_data.csv
    drivers.csv
    driver_goals.csv
    trips.csv
    flagged_moments.csv
    earnings_velocity_log.csv
    uber_processed_output.csv

src/
    app.py
    simulator.py
    safety_engine.py
    financial_engine.py
    generate_synthetic_data.py
    generate_uber_submission_log.py

requirements.txt
README.md
```

---

# Core Components

## 1. Synthetic Data Generator

`generate_synthetic_data.py`

Creates a **complete simulated driver shift dataset**.

Generated artifacts:

- driver profile
- shift goals
- trip metadata
- per-second accelerometer stream
- per-second audio stream

The dataset includes **nine trips with injected anomalies** to stress-test detection logic.

Examples include:

- harsh braking at highway speed
- device drop acceleration spike
- sustained loud audio
- braking inside a tunnel (GPS dropout)
- passenger conflict signal (brake + loud audio)

---

## 2. Event Stream Simulator

`simulator.py`

The simulator merges the sensor streams into a **chronological event stream**.

Processing flow:

1. Load accelerometer and audio streams
2. Tag events by type
3. Merge and sort by timestamp
4. Replay events sequentially
5. Dispatch events to engines

Event routing:

```
motion events → SafetyEngine.process_motion()

audio events → SafetyEngine.process_audio()

trip completion → FinancialEngine.process_completed_trip()
```

The loop runs with a short delay (`sleep(0.005)`) so the shift simulation completes quickly for demo purposes.

---

## 3. Safety Engine

`safety_engine.py`

The safety engine processes telemetry signals using **deterministic heuristics and sliding time windows**.

Signals analyzed:

### Motion

Linear acceleration is computed using:

```
a = sqrt(ax² + ay² + (az − g)²)
```

Detected events:

- harsh braking
- repeated braking
- abnormal acceleration spikes

Safety filters include:

- ignoring spikes while vehicle speed < 5 km/h
- cooldown windows between alerts
- time-window smoothing

### Audio

Cabin audio signals detect sustained elevated noise levels.

This can represent:

- loud music
- arguments
- high passenger activity

### Conflict Detection

If both signals occur within a short time window:

```
harsh braking
+
sustained high audio
```

the system flags a **conflict moment**.

All safety events are written to:

```
data/flagged_moments.csv
```

---

## 4. Financial Engine

`financial_engine.py`

Tracks driver shift performance and calculates:

- cumulative earnings
- earnings velocity ($/hour)
- required velocity to hit target
- forecast status
- estimated trips remaining

Forecast states:

| Status | Meaning |
|------|------|
AHEAD | Driver is ahead of pace |
ON_TRACK | Driver is near target pace |
BEHIND | Driver must increase pace |
ACHIEVED | Earnings goal reached |

Financial metrics are logged to:

```
data/earnings_velocity_log.csv
```

---

## 5. Submission Log Generator

`generate_uber_submission_log.py`

The hackathon deliverable requires a **single consolidated output file**.

Rather than modifying the already-validated safety and financial engines late in development, a **post-processing step** was introduced to aggregate their outputs.

This script reads:

```
flagged_moments.csv
earnings_velocity_log.csv
```

and produces the unified submission file:

```
uber_processed_output.csv
```

This approach was chosen to:

- avoid regression risk in working engines
- preserve modular system design
- keep the submission pipeline deterministic

Execution of this step should occur **after the simulator completes**.

---

# Dashboard

`app.py`

The frontend uses **Streamlit**.

Two primary interfaces are provided.

---

## Live Shift

Designed for minimal driver distraction.

Displays:

- current earnings
- earnings velocity
- forecast status
- goal progress
- estimated remaining trips

---

## Pit Stop Analytics

Post-shift analysis view.

Includes:

- earnings vs ideal pace chart
- trip-by-trip financial breakdown
- safety score
- filterable event log

Safety score is derived from event severity.

---

# Trade-offs & Assumptions

### Deterministic Heuristics vs Machine Learning

For this prototype, safety detection is implemented using **rule-based thresholds rather than ML models**.

Advantages:

- predictable behavior
- faster development
- transparent logic for debugging
- no training data requirement

Trade-off:

- less adaptive than learned models
- thresholds must be tuned manually.

---

### Synthetic Telemetry Data

Sensor inputs are generated artificially.

Assumptions made:

- accelerometer noise follows a normal distribution
- audio signals approximate cabin noise patterns
- trip durations and fares approximate real driving conditions

Trade-off:

The dataset is idealized and may not capture the full variability of real telemetry streams.

---

### CSV-based Event Logging

The prototype uses CSV logs instead of streaming infrastructure.

Advantages:

- simplicity
- easy inspection
- fast local iteration

Trade-off:

In production this would be replaced by:

- Kafka streams
- WebSocket event buses
- real-time telemetry ingestion.

---

### Post-processing Submission Log

The unified output file is generated using a **post-processing step** rather than direct engine integration.

This design was intentionally chosen to:

- preserve stability of working components
- keep system modules loosely coupled
- ensure reproducible submission output

---

# Next Engineering Steps

Potential improvements if the system were extended:

1. Replace CSV logs with event streaming infrastructure
2. Integrate real mobile sensor telemetry
3. Train ML models for behavioral driving detection
4. Add fleet-level monitoring dashboards
5. Deploy backend services for multi-driver support

---

# Author

Divyam Nagpal – IIT (BHU) Varanasi  
Nevica Gupta – IGDTUW  
Chirag – IIT Roorkee  
