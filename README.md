# GASROUTE 2030

**From Flare Data to Gas-to-Value Decisions**  
*Strategic Screening MVP Prototype for the Nigerian Oil and Gas firms.

## 📋 Project Overview
GASROUTE 2030 is an automated midstream monetization screening engine designed to eliminate routine gas flaring across onshore and swamp assets in the Nigerian Niger Delta by 2030. Built in alignment with the Petroleum Industry Act (PIA) and NUPRC regulatory frameworks, the simulator processes variable asset characteristics (volume, chemistry, and location infrastructure) to identify optimal engineering skids and commercial funding pathways.

## 🛠️ Architecture & Tech Stack
The platform uses a modular 5-file decoupled Python structure to split frontend rendering from backend mathematical processing:
- `app.py`: Interactive user dashboard and Session State synchronization engine built with **Streamlit**.
- `calculations.py`: Process engineering thermodynamics modeling compressor duty (kW) and recovery limits.
- `routes.py`: Point-scoring optimization loops for five monetization pathways (CNG, LNG, Power, LPG/NGL, Reinjection).
- `economics.py`: Capital allocation matrix accounting for Unincorporated JOA Equity shares and asset financial metrics.
- `data/facilities.csv`: Niger Delta preset asset profiles modeled from active fields.

## 🚀 Local Execution
To run the dashboard sandbox locally, install dependencies and execute the script via terminal:
```bash
pip install -r requirements.txt
python -m streamlit run app.py
```
