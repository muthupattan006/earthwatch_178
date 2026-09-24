import React, { useEffect, useState } from 'react';
import Plot from 'react-plotly.js';
import axios from 'axios';

const API =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const SENSOR_CONFIG = {
  temperature: {
    title: 'Temperature',
    unit: '°C',
  },
  humidity: {
    title: 'Humidity',
    unit: '%',
  },
  pressure: {
    title: 'Pressure',
    unit: 'hPa',
  },
  water_level: {
    title: 'Water Level',
    unit: 'm',
  },
  water_rate: {
    title: 'Water Rate',
    unit: 'm/s',
  },
  soil_moisture: {
    title: 'Soil Moisture',
    unit: '',
  },
  tilt_x: {
    title: 'Tilt X',
    unit: '°',
  },
  tilt_y: {
    title: 'Tilt Y',
    unit: '°',
  },
  tilt_rate: {
    title: 'Tilt Rate',
    unit: '°/s',
  },
  mq2: {
    title: 'MQ2 Gas',
    unit: 'ppm',
  },
};

export default function Nowcast({ node }) {
  const [nowcastData, setNowcastData] = useState(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let alive = true;

    const fetchNowcast = async () => {
      try {
        const response = await axios.get(
          API + '/api/nowcast',
          {
            params: {
              latitude: node.lat,
              longitude: node.lng,
            },
          }
        );

        if (!alive) return;

        setNowcastData(response.data);
        setConnected(true);
        setError('');
      } catch (err) {
        if (!alive) return;

        setConnected(false);
        setError('Waiting for backend / sensor data...');
      }
    };

    fetchNowcast();

    const interval = setInterval(
      fetchNowcast,
      2000
    );

    return () => {
      alive = false;
      clearInterval(interval);
    };
  }, [node.lat, node.lng]);

  const sensors = Object.keys(SENSOR_CONFIG);

  return (
    <main className="page">

      <div className="page-head">
        <div>
          <div className="eyebrow">
            NOWCASTING
          </div>

          <h1>
            {node.name} · Live Nowcasting
          </h1>

          <p>
            Real-time sensor observations and
            short-term nowcast predictions for the
            selected location.
          </p>

          <p
            style={{
              marginTop: '6px',
              fontSize: '13px',
              opacity: 0.7,
            }}
          >
            Location: {node.lat}, {node.lng}
          </p>
        </div>

        <span
          className={
            'chip ' + (connected ? 'live' : '')
          }
        >
          {connected
            ? '● LIVE'
            : '○ WAITING FOR DATA'}
        </span>
      </div>

      {error && (
        <div
          style={{
            padding: '14px 16px',
            marginBottom: '18px',
            borderRadius: '10px',
            background:
              'rgba(255, 193, 7, 0.08)',
            border:
              '1px solid rgba(255, 193, 7, 0.25)',
          }}
        >
          {error}
        </div>
      )}

      {nowcastData &&
        nowcastData.risk && (
          <RiskCard
            risk={nowcastData.risk}
          />
        )}

      <div className="live-grid">
        {sensors.map((sensor) => (
          <NowcastChart
            key={sensor}
            sensor={sensor}
            data={
              nowcastData &&
              nowcastData.sensors
                ? nowcastData.sensors[sensor]
                : null
            }
          />
        ))}
      </div>

    </main>
  );
}

function RiskCard({ risk }) {
  return (
    <section
      className="live-card"
      style={{
        marginBottom: '20px',
      }}
    >
      <div className="graph-title">
        Current Risk Assessment
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns:
            'repeat(3, 1fr)',
          gap: '16px',
          marginTop: '12px',
        }}
      >

        <div>
          <div
            style={{
              opacity: 0.65,
              fontSize: '12px',
            }}
          >
            RISK SCORE
          </div>

          <div
            style={{
              fontSize: '28px',
              fontWeight: 700,
              marginTop: '4px',
            }}
          >
            {risk.score !== undefined
              ? risk.score
              : '--'}
          </div>
        </div>

        <div>
          <div
            style={{
              opacity: 0.65,
              fontSize: '12px',
            }}
          >
            STATUS
          </div>

          <div
            style={{
              fontSize: '20px',
              fontWeight: 600,
              marginTop: '7px',
            }}
          >
            {risk.status || '--'}
          </div>
        </div>

        <div>
          <div
            style={{
              opacity: 0.65,
              fontSize: '12px',
            }}
          >
            HAZARD
          </div>

          <div
            style={{
              fontSize: '20px',
              fontWeight: 600,
              marginTop: '7px',
            }}
          >
            {risk.hazard || '--'}
          </div>
        </div>

      </div>
    </section>
  );
}

function NowcastChart({ sensor, data }) {
  const config = SENSOR_CONFIG[sensor];

  if (!data) {
    return (
      <article className="live-card">

        <div className="graph-title">
          {config.title}

          {config.unit && (
            <span
              style={{
                fontSize: '12px',
                opacity: 0.6,
                marginLeft: '6px',
              }}
            >
              ({config.unit})
            </span>
          )}
        </div>

        <div
          style={{
            height: '280px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            opacity: 0.5,
          }}
        >
          Waiting for data...
        </div>

      </article>
    );
  }

  const observed = data.observed || [];
  /*const nowcast = data.nowcast || [];*/

  const observedX = observed.map(
    (point) =>
      point.timestamp || point.time
  );

  const observedY = observed.map(
    (point) => point.value
  );

  {/*const nowcastX = nowcast.map(
    (point) =>
      point.timestamp || point.time
  );

  const nowcastY = nowcast.map(
    (point) => point.value
  );*/}

  const traces = [];

  if (observed.length > 0) {
    traces.push({
      x: observedX,
      y: observedY,
      type: 'scatter',
      mode: 'lines+markers',
      name: 'Observed',
      connectgaps: false,
      line: {
        width: 2,
      },
      marker: {
        size: 4,
      },
    });
  }

  {/*if (nowcast.length > 0) {
    traces.push({
      x: nowcastX,
      y: nowcastY,
      type: 'scatter',
      mode: 'lines',
      name: 'Nowcast',
      connectgaps: false,
      line: {
        width: 3,
        dash: 'dash',
      },
    });
  }*/}

  return (
    <article className="live-card">

      <div className="graph-title">
        {config.title}

        {config.unit && (
          <span
            style={{
              fontSize: '12px',
              opacity: 0.6,
              marginLeft: '6px',
            }}
          >
            ({config.unit})
          </span>
        )}
      </div>

      {traces.length === 0 ? (
        <div
          style={{
            height: '280px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            opacity: 0.5,
          }}
        >
          No sensor data yet
        </div>
      ) : (
        <Plot
          data={traces}
          layout={{
            autosize: true,
            height: 300,

            margin: {
              l: 55,
              r: 20,
              t: 15,
              b: 50,
            },

            hovermode: 'x unified',

            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',

            xaxis: {
              title: 'Time',
              showgrid: true,
            },

            yaxis: {
              title: config.unit
                ? config.title +
                  ' (' +
                  config.unit +
                  ')'
                : config.title,
              showgrid: true,
            },

            legend: {
              orientation: 'h',
              y: 1.08,
              x: 0,
            },
          }}

          config={{
            responsive: true,
            displaylogo: false,
          }}

          style={{
            width: '100%',
          }}
        />
      )}

    </article>
  );
}