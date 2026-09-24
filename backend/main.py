from collections import defaultdict, deque
from datetime import datetime, timezone
import asyncio, json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from Live_data.nowcasting import get_live_nowcast
from Live_data.live_data import start_live_data, stop_live_data

app=FastAPI(title='Earthwatch Local Sensor API')
@app.on_event("startup")
def startup_event():
    print("[EARTHWATCH] Starting ESP32 live-data reader...")
    started = start_live_data()

    if started:
        print("[EARTHWATCH] ESP32 live-data reader started.")
    else:
        print("[EARTHWATCH] ESP32 live-data reader could not start.")


@app.on_event("shutdown")
def shutdown_event():
    print("[EARTHWATCH] Stopping ESP32 live-data reader...")
    stop_live_data()
app.add_middleware(CORSMiddleware,allow_origins=['http://localhost:5173'],allow_credentials=True,allow_methods=['*'],allow_headers=['*'])
BUFFER=defaultdict(lambda: defaultdict(lambda: deque(maxlen=120)))
CLIENTS=defaultdict(set)

class Reading(BaseModel):
    node_id:str
    sensor:str
    timestamp:str|None=None
    value:float
    unit:str|None=None
    metadata:dict|None=None

@app.get('/api/health')
def health(): return {'status':'ok','service':'earthwatch-sensor-api'}

@app.get("/api/nowcast")
def nowcast(latitude: float | None = None, longitude: float | None = None):
    return get_live_nowcast(
        latitude=latitude,
        longitude=longitude
    )

@app.post('/api/sensor-data')
async def ingest(r:Reading):
    item=r.model_dump(); item['timestamp']=item['timestamp'] or datetime.now(timezone.utc).isoformat(); BUFFER[r.node_id][r.sensor].append(item)
    dead=[]
    for ws in CLIENTS[r.node_id]:
        try: await ws.send_text(json.dumps(item))
        except Exception: dead.append(ws)
    for ws in dead: CLIENTS[r.node_id].discard(ws)
    return {'stored':True,'buffer_size':len(BUFFER[r.node_id][r.sensor])}

@app.get('/api/nodes/{node_id}/sensors')
def node_sensors(node_id:str): return {'node_id':node_id,'streams':{s:list(v) for s,v in BUFFER[node_id].items()}}

@app.websocket('/ws/nowcast/{node_id}')
async def nowcast_ws(ws:WebSocket,node_id:str):
    await ws.accept(); CLIENTS[node_id].add(ws)
    try:
        for sensor,values in BUFFER[node_id].items():
            for item in values: await ws.send_text(json.dumps(item))
        while True: await ws.receive_text()
    except WebSocketDisconnect: pass
    finally: CLIENTS[node_id].discard(ws)
