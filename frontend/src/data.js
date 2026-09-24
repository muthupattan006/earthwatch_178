export const NODES = [
  { id:'PAN-01', name:'Panthalur', lat:11.4865, lng:76.3396, radiusKm:8.33, cities:['Pandalur Town','Nelliyalam','Devala','Uppatti','Cherangode','Kolapalli','Ayankolly','Nellakotta','Erumad','Nadugani','Devarshola'] },
  { id:'GUD-01', name:'Gudalur', lat:11.5007, lng:76.4921 },
  { id:'UDG-01', name:'Udagamandalam', lat:11.4118, lng:76.7023 },
  { id:'KOT-01', name:'Kothagiri', lat:11.4207, lng:76.8603 },
  { id:'COO-01', name:'Coonoor', lat:11.3450, lng:76.7950 },
  { id:'KUN-01', name:'Kundah', lat:11.2810, lng:76.6499 }
];

export const FORECAST_GRAPHS = [
  ['Temperature','/forecasting/temperature_forecast.html'],
  ['Humidity & Cloudiness','/forecasting/humidity_cloudiness_forecast.html'],
  ['Rainfall','/forecasting/rainfall_forecast.html'],
  ['Surface Pressure Deviation','/forecasting/surface_pressure_deviation.html'],
  ['Wind','/forecasting/wind_forecast.html']
];

export const SENSOR_GROUPS = {
  Flood: ['RGN-11','JSN-SR04T','NEO-6'],
  Landslide: ['Soil moisture','Geophone','SW-420','RG-11'],
  'Forest fire': ['SCD-40','PM2.5','ZE07-CO','NEO-6'],
  'Air Quality': ['STX-35','PM2.5','NEO-6','SCD-40']
};

// Static calibration / danger thresholds per node, in the same param shape
// classify() expects (see hazards.js). These are the fixed reference values
// (slope, danger level, full-tank level, etc.) that don't come from a sensor
// reading each second — only the live fields get overwritten by hardware data
// in useNetworkAlerts.js. Tune these to each node's real site survey data.
//
// Only include a hazard block for a node if that hazard is physically
// relevant there (e.g. skip lake_water_level for nodes with no reservoir).
export const HAZARD_PARAMS = {
  'PAN-01': {
    landslide: { slope_deg: 32, soil_moisture_pct: 30, rainfall_24h_mm: 0 },
    flood: { danger_level_m: 3.5, river_level_m: 0, rainfall_24h_mm: 0 },
  },
  'GUD-01': {
    landslide: { slope_deg: 28, soil_moisture_pct: 28, rainfall_24h_mm: 0 },
    forest_fire: { rel_humidity_pct: 40, rain_gauge_7d_mm: 0, frp_mw: 0, aqi: 0 },
  },
  'UDG-01': {
    industrial_emission: { pm25_ugm3: 0, co_ppm: 0, so2_ugm3: 0 },
    heat_wave: { max_temp_c: 0, departure_c: 0, heat_index_c: 0 },
  },
  'KOT-01': {
    landslide: { slope_deg: 34, soil_moisture_pct: 30, rainfall_24h_mm: 0 },
  },
  'COO-01': {
    thunderstorm: { gust_kmph: 0, lightning_strikes_hr: 0 },
    forest_fire: { rel_humidity_pct: 40, rain_gauge_7d_mm: 0, frp_mw: 0, aqi: 0 },
  },
  'KUN-01': {
    lake_water_level: { full_tank_level_ft: 24.0, level_ft: 0, storage_pct: 0, inflow_cusecs: 0 },
    landslide: { slope_deg: 30, soil_moisture_pct: 28, rainfall_24h_mm: 0 },
  },
};

// Maps a live sensor name (as used in SENSOR_GROUPS / your WebSocket stream
// key) to the classify() param field it should overwrite for a given
// hazard. Adjust this table once you know your Arduino payload's exact
// units/scaling — this is the one place hardware wiring plugs in.
export const SENSOR_TO_PARAM = {
  'RGN-11':        { hazard: 'flood',       param: 'rainfall_24h_mm' },
  'JSN-SR04T':      { hazard: 'flood',       param: 'river_level_m' },
  'RG-11':          { hazard: 'landslide',   param: 'rainfall_24h_mm' },
  'Soil moisture':  { hazard: 'landslide',   param: 'soil_moisture_pct' },
  'PM2.5':          { hazard: 'industrial_emission', param: 'pm25_ugm3' },
  'ZE07-CO':        { hazard: 'industrial_emission', param: 'co_ppm' },
  'SCD-40':         { hazard: 'forest_fire', param: 'rel_humidity_pct' },
};
