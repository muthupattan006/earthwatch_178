import { useEffect, useMemo, useRef, useState } from 'react';
import axios from 'axios';
import { NODES, HAZARD_PARAMS, SENSOR_TO_PARAM } from '../data';
import { buildAlerts } from '../hazards';

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Opens the same per-node sensor API + WebSocket connection Nowcast.jsx
// uses, but for every node at once, and folds each live reading into the
// matching hazard's params via SENSOR_TO_PARAM. Returns a classified,
// sorted alert list for the whole network, refreshed as readings arrive.
export default function useNetworkAlerts() {
  // live[nodeId][hazard][param] = latest numeric value from hardware
  const [live, setLive] = useState({});
  const socketsRef = useRef([]);

  useEffect(() => {
    let alive = true;
    const sockets = [];

    NODES.forEach((node) => {
      axios
        .get(`${API}/api/nodes/${node.id}/sensors`)
        .then((r) => {
          if (!alive) return;
          const streams = r.data.streams || {};
          Object.entries(streams).forEach(([sensor, points]) => {
            const last = points?.[points.length - 1];
            if (last) applyReading(node.id, sensor, last.value, setLive);
          });
        })
        .catch(() => {});

      try {
        const ws = new WebSocket(
          API.replace(/^http/, 'ws') + `/ws/nowcast/${node.id}`
        );
        ws.onmessage = (e) => {
          const d = JSON.parse(e.data);
          applyReading(node.id, d.sensor, d.value, setLive);
        };
        sockets.push(ws);
      } catch {
        /* backend not reachable yet — alerts fall back to baseline params */
      }
    });

    socketsRef.current = sockets;
    return () => {
      alive = false;
      sockets.forEach((ws) => ws.close());
    };
  }, []);

  const alerts = useMemo(() => {
    const nodesById = Object.fromEntries(NODES.map((n) => [n.id, n]));

    // Only build an alert for a hazard once real live sensor data has
    // arrived for it — baseline HAZARD_PARAMS alone (no live override) do
    // NOT produce an alert. This keeps the panel/map empty until nowcast
    // data is actually flowing from the hardware.
    const merged = {};
    for (const node of NODES) {
      const base = HAZARD_PARAMS[node.id] || {};
      const overrides = live[node.id] || {};
      const hazards = {};
      for (const hazard of Object.keys(overrides)) {
        hazards[hazard] = { ...(base[hazard] || {}), ...overrides[hazard] };
      }
      if (Object.keys(hazards).length) merged[node.id] = hazards;
    }

    return buildAlerts(merged, nodesById);
  }, [live]);

  return alerts;
}

function applyReading(nodeId, sensor, value, setLive) {
  const mapping = SENSOR_TO_PARAM[sensor];
  if (!mapping || value === undefined || value === null) return;
  setLive((prev) => ({
    ...prev,
    [nodeId]: {
      ...prev[nodeId],
      [mapping.hazard]: {
        ...(prev[nodeId]?.[mapping.hazard] || {}),
        [mapping.param]: value,
      },
    },
  }));
}
