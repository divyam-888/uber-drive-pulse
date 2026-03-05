# uber-drive-pulse

# Uber Drive Pulse

Uber Drive Pulse is a real-time safety and financial telemetry system designed for gig-economy drivers. Built for the Uber Engineering Hackathon 2026, this platform utilizes an event-driven architecture to process high-frequency sensor data and financial metrics. It provides drivers with a distraction-free live dashboard during their shift, and comprehensive, filterable analytics during their post-ride review.

## Core Features

* **Stateful Stream Processing:** Ingests high-frequency accelerometer and audio data to detect anomalous driving behaviors (harsh braking, device drops, cabin conflicts) using rolling time-windows.
* **Context-Aware Physics:** Utilizes GPS speed filtering to eliminate false positives, ensuring events like door slams while parked are not flagged as collisions.
* **Dynamic Financial Ledger:** Continuously calculates "Earnings Velocity" and projects goal completion based on historical shift data, adjusting the required pace in real-time.
* **Cognitive Load Management:** The frontend is strictly divided into a minimalist "Live Shift" view to prevent driver distraction, and a deep-dive "Pit Stop Analytics" view for behavioral review.

## Directory Structure

```text
uber-drive-pulse/
├── data/                               # Local database (Generated CSVs)
├── src/
│   ├── app.py                          # Streamlit frontend dashboard
│   ├── financial_engine.py             # Earnings & velocity computations
│   ├── safety_engine.py                # Sensor anomaly detection logic
│   ├── simulator.py                    # The master event-loop dispatcher
│   └── generate_synthetic_data.py      # 9-trip edge-case dataset generator
├── .streamlit/
│   └── config.toml                     # UI theme and styling configuration
├── requirements.txt                    # Project dependencies
└── README.md
```

## Installation & Local Setup

Ensure you have Python 3.8+ installed on your machine.

1. **Clone the Repository**
```bash
git clone https://github.com/YourUsername/uber-drive-pulse.git
cd uber-drive-pulse
```

2. **Create Virtual Environment (Optional)**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install Requirements**
```bash
pip install -r requirements.txt
```

## Running the Application

This is an event-driven system. To view the full live pipeline locally, you must utilize two separate terminal windows to run the frontend and backend simultaneously.

1. **Initialize Data and Frontend**
In your first terminal, generate the synthetic test data and start the user interface.
```bash
python src/generate_synthetic_data.py
streamlit run src/app.py
```
_Your browser will automatically open the dashboard. Leave it on the "Live Shift" tab. It will display a waiting state._

2. **Trigger the Backend Simulator**
```bash
python src/simulator.py
```

_As the backend processes the simulated trips in the terminal, the Streamlit dashboard in your browser will automatically poll the new data and animate the progress bars and charts in real-time._

