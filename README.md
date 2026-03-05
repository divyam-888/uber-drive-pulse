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