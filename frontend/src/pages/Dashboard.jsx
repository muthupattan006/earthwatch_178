import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import MapView from '../components/MapView';
import Legend from '../components/Legend';
import AlertPanel from '../components/AlertPanel';
import useNetworkAlerts from '../hooks/useNetworkAlerts';

export default function Dashboard({ node, setNodeId }) {
  const [showAnalysis, setShowAnalysis] = useState(false);
  const alerts = useNetworkAlerts();

  const handleNodeSelect = (id) => {
    setNodeId(id);
    setShowAnalysis(true);
  };

  const handleFocusAlert = (alert) => {
    setNodeId(alert.nodeId);
    setShowAnalysis(true);
  };

  return (
    <main className="dashboard">
      <section className="map-stage">

        <MapView
          node={node}
          onNodeSelect={handleNodeSelect}
        />

        {showAnalysis && (
          <LocationAnalysisPopup
            node={node}
            onClose={() => setShowAnalysis(false)}
          />
        )}

        <AlertPanel alerts={alerts} onFocusAlert={handleFocusAlert} />

        <Legend />

        <div className="map-caption">
          NILGIRIS MONITORING NETWORK · {node.name.toUpperCase()}
        </div>

      </section>
    </main>
  );
}


function LocationAnalysisPopup({ node, onClose }) {
  const navigate = useNavigate();

  const openPage = (page) => {
    onClose();
    navigate(page);
  };

  return (
    <div className="analysis-popup">

      <button
        className="popup-close"
        onClick={onClose}
        aria-label="Close"
      >
        ×
      </button>

      <div className="popup-location">

        <div className="popup-pin">
          ●
        </div>

        <div>
          <div className="popup-eyebrow">
            SELECTED MONITORING NODE
          </div>

          <h2>{node.name}</h2>

          <div className="popup-coordinates">
            {node.lat.toFixed(4)}°N · {node.lng.toFixed(4)}°E
          </div>

          {node.radiusKm && (
            <div className="popup-radius">
              Monitoring Radius:{' '}
              <b>{node.radiusKm} km</b>
            </div>
          )}
        </div>

      </div>

      <div className="popup-divider" />

      <div className="popup-title">
        SELECT ANALYSIS
      </div>

      <button
        className="analysis-option"
        onClick={() => openPage('/forecast')}
      >
        <div className="analysis-icon forecast-icon">
          ↗
        </div>

        <div>
          <strong>Forecasting</strong>
          <span>
            Predictive weather variables
          </span>
        </div>

        <b className="analysis-arrow">
          →
        </b>
      </button>

      <button
        className="analysis-option"
        onClick={() => openPage('/nowcast')}
      >
        <div className="analysis-icon nowcast-icon">
          ◉
        </div>

        <div>
          <strong>Nowcasting</strong>
          <span>
            Live sensor conditions
          </span>
        </div>

        <b className="analysis-arrow">
          →
        </b>
      </button>

      <button
        className="analysis-option"
        onClick={() => openPage('/historical')}
      >
        <div className="analysis-icon historical-icon">
          ≋
        </div>

        <div>
          <strong>Historical / Trend</strong>
          <span>
            Past observations and trends
          </span>
        </div>

        <b className="analysis-arrow">
          →
        </b>
      </button>

    </div>
  );
}
