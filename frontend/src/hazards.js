// Port of the Python hazard_alert_map.py classification logic.
// Keeps the same hazard keys, level colors, and threshold rules so the
// EarthWatch dashboard alerts stay consistent with the standalone map tool.

export const LEVEL_COLORS = {
  low:    { bg: '#FFE000', fg: '#1a1a1a', name: 'Watch' },
  medium: { bg: '#FF8C1A', fg: '#ffffff', name: 'Alert' },
  high:   { bg: '#E02020', fg: '#ffffff', name: 'Warning' },
};

export const HAZARD_META = {
  landslide:            { icon: '🪨', label: 'Landslide' },
  flood:                { icon: '🌊', label: 'Flood' },
  industrial_emission:  { icon: '🏭', label: 'Industrial Emission' },
  forest_fire:          { icon: '🔥', label: 'Forest Fire' },
  heat_wave:            { icon: '🌡', label: 'Heat Wave' },
  lake_water_level:     { icon: '💧', label: 'Lake Water Level' },
  thunderstorm:         { icon: '⛈', label: 'Thunderstorm' },
};

export const LEVEL_ORDER = { high: 0, medium: 1, low: 2 };

function scoreToLevel(score, highCut, medCut) {
  if (score >= highCut) return 'high';
  if (score >= medCut) return 'medium';
  return 'low';
}

// classify(hazard, params) -> { level, reason }
// params is a plain object of numeric readings, keyed the same way as the
// Python RAW_OBSERVATIONS[i].params dicts (see data.js HAZARD_PARAMS).
export function classify(hazard, p = {}) {
  const g = (k, d = 0) => (p[k] !== undefined && p[k] !== null ? p[k] : d);

  if (hazard === 'landslide') {
    let score = 0;
    if (g('rainfall_24h_mm') >= 115) score += 2;
    else if (g('rainfall_24h_mm') >= 64) score += 1;
    if (g('slope_deg') >= 35) score += 2;
    else if (g('slope_deg') >= 25) score += 1;
    if (g('soil_moisture_pct') >= 45) score += 1;
    const reason = `Rainfall ${g('rainfall_24h_mm')} mm/24h on ${g('slope_deg')}deg slope, soil moisture ${g('soil_moisture_pct')}%`;
    return { level: scoreToLevel(score, 4, 2), reason };
  }

  if (hazard === 'flood') {
    const lvl = g('river_level_m');
    const dgr = g('danger_level_m', Infinity);
    const warn = dgr - 1.0;
    let level = lvl >= dgr ? 'high' : lvl >= warn ? 'medium' : 'low';
    if (g('rainfall_24h_mm') >= 115 && level === 'low') level = 'medium';
    const reason = `Gauge ${lvl} m vs danger ${dgr} m; rainfall ${g('rainfall_24h_mm')} mm/24h`;
    return { level, reason };
  }

  if (hazard === 'industrial_emission') {
    const pm = g('pm25_ugm3');
    let level = 'low';
    if (pm >= 121 || g('co_ppm') >= 9) level = 'high';
    else if (pm >= 61) level = 'medium';
    const reason = `PM2.5 ${pm} ug/m3, CO ${g('co_ppm')} ppm, SO2 ${g('so2_ugm3')} ug/m3`;
    return { level, reason };
  }

  if (hazard === 'forest_fire') {
    const frp = g('frp_mw');
    let level = 'low';
    if (frp >= 50 && g('rel_humidity_pct', 100) < 30) level = 'high';
    else if (frp >= 15) level = 'medium';
    const reason = `FRP ${frp} MW, RH ${g('rel_humidity_pct')}%, AQI ${g('aqi')}, 7-day rain ${g('rain_gauge_7d_mm')} mm`;
    return { level, reason };
  }

  if (hazard === 'heat_wave') {
    const d = g('departure_c');
    let level = 'low';
    if (d > 6.4 || g('max_temp_c') >= 47) level = 'high';
    else if (d >= 4.5) level = 'medium';
    const reason = `Max ${g('max_temp_c')} C, departure +${d} C, heat index ${g('heat_index_c')} C`;
    return { level, reason };
  }

  if (hazard === 'lake_water_level') {
    const pct = g('storage_pct');
    let level = 'low';
    if (pct >= 95) level = 'high';
    else if (pct >= 80) level = 'medium';
    const reason = `Storage ${pct}% (${g('level_ft')} / ${g('full_tank_level_ft')} ft), inflow ${g('inflow_cusecs')} cusecs`;
    return { level, reason };
  }

  if (hazard === 'thunderstorm') {
    const gust = g('gust_kmph');
    let level = 'low';
    if (gust >= 60) level = 'high';
    else if (gust >= 40) level = 'medium';
    const reason = `Gusts ${gust} km/h, ${g('lightning_strikes_hr')} strikes/hr`;
    return { level, reason };
  }

  return { level: 'low', reason: 'No rule defined' };
}

// Build a sorted alert list from { nodeId -> { hazard -> params } } style input.
// Each entry: { hazard, place, lat, lng, level, reason, params, nodeId }
export function buildAlerts(nodeHazardParams, nodesById) {
  const alerts = [];
  for (const [nodeId, hazardMap] of Object.entries(nodeHazardParams)) {
    const node = nodesById[nodeId];
    if (!node) continue;
    for (const [hazard, params] of Object.entries(hazardMap)) {
      const { level, reason } = classify(hazard, params);
      alerts.push({
        hazard,
        place: node.name,
        lat: node.lat,
        lng: node.lng,
        nodeId,
        level,
        reason,
        params,
      });
    }
  }
  alerts.sort((a, b) => (LEVEL_ORDER[a.level] - LEVEL_ORDER[b.level]) || a.hazard.localeCompare(b.hazard));
  return alerts;
}
