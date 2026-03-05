# uber-drive-pulse

Uber Drive Pulse
Uber Drive Pulse is a real-time safety and financial telemetry system designed for gig-economy drivers. Built for the Uber Engineering Hackathon 2026, this platform utilizes an event-driven architecture to process high-frequency sensor data and financial metrics, providing drivers with a distraction-free live dashboard and comprehensive post-shift analytics.

Core Features
Stateful Stream Processing: Processes high-frequency accelerometer and audio data in real-time to detect anomalous driving behaviors (e.g., harsh braking, device drops, cabin conflicts) without relying on heavy machine learning models.

Context-Aware Safety Engine: Uses GPS speed filtering to eliminate false positives (such as logging a door slam while parked as a collision).

Dynamic Financial Ledger: Continuously calculates "Earnings Velocity" and projects goal completion based on historical shift data, dynamically adjusting the required pace.

Cognitive Load Management: The frontend is strictly divided into a minimalist "Live Shift" view to prevent driver distraction, and a deep-dive "Pit Stop Analytics" view for post-ride behavioral review.

System Architecture
The project is decoupled into three primary micro-services:

Synthetic Data Generator: Creates rigorous, high-frequency driving data containing orchestrated edge cases for system backtesting.

Backend Engine (Simulator): A Python-based event loop that ingests sensor streams, applies physical and financial heuristics, and writes events to local data logs.

Frontend Dashboard: A Streamlit application that polls the backend data logs to render live, interactive charts and metrics.

Installation and Local Setup
To run this project locally, ensure you have Python 3.8+ installed.

1. Clone the repository

Bash
git clone https://github.com/yourusername/uber-drive-pulse.git
cd uber-drive-pulse
2. Set up the virtual environment
For macOS/Linux:

Bash
python3 -m venv venv
source venv/bin/activate
For Windows:

DOS
python -m venv venv
venv\Scripts\activate
3. Install dependencies

Bash
pip install -r requirements.txt
Running the Application
This is an event-driven system. To view the full live pipeline locally, you will utilize two terminal windows.

Step 1: Initialize Data and Frontend
In your first terminal, generate the synthetic test data and start the user interface.

Bash
python src/generate_synthetic_data.py
streamlit run src/app.py
Step 2: Trigger the Backend Simulator
Open a second terminal window, activate your virtual environment, and execute the event loop.

Bash
python src/simulator.py
As the backend processes the simulated trips, the Streamlit dashboard in your browser will automatically poll the new data and animate in real-time.

Cloud Deployment
A live version of this application is hosted via Streamlit Community Cloud.

You can access the deployed dashboard here: [https://uber-drive-pulse.streamlit.app/]
