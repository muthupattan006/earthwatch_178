# Earthwatch Dashboard — starter implementation

## What is already wired
- Google Maps satellite map with six Nilgiris monitoring nodes.
- Node selector and smooth pan/zoom to the selected node.
- Panthalur location card with the supplied radius/city metadata.
- Analysis navigation: Forecasting / Nowcasting / Historical-Trend.
- Uploaded forecasting HTML graphs preserved under `frontend/public/forecasting/` and displayed as-is.
- Nowcasting architecture uses a real local FastAPI buffer + WebSocket; no synthetic nowcast values are generated.
- Generic `POST /api/sensor-data` ingestion endpoint for the hardware gateway.
- Live Plotly charts for sensor streams.
- Hazard legend and severity styling inspired by the supplied Folium map.

## Run
1. Install Node.js and Python.
2. In `frontend`, copy `.env.example` to `.env` and put your Google Maps API key in `VITE_GOOGLE_MAPS_API_KEY` locally.
3. Install frontend dependencies: `npm install` inside `frontend`.
4. Install root dependency: `npm install` in the project root (for concurrently), or run frontend/backend separately.
5. Backend: `cd backend && pip install -r requirements.txt && python -m uvicorn main:app --reload --port 8000`
6. Frontend: `cd frontend && npm run dev`

## Hardware ingestion
Send JSON readings to `POST http://localhost:8000/api/sensor-data`, e.g.
`{"node_id":"PAN-01","sensor":"RGN-11","value":1.47,"unit":"m","timestamp":"2026-09-21T13:45:04+05:30"}`

The transport from the physical sensor/controller to this HTTP endpoint is intentionally left as an adapter because the final hardware communication protocol has not yet been specified.
