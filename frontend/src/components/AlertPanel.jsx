import React, { useState } from 'react';
import { HAZARD_META, LEVEL_COLORS } from '../hazards';

export default function AlertPanel({ alerts, onFocusAlert }) {
  const [filter, setFilter] = useState('all');
  const [open, setOpen] = useState(true);

  const counts = {
    high: alerts.filter((a) => a.level === 'high').length,
    medium: alerts.filter((a) => a.level === 'medium').length,
    low: alerts.filter((a) => a.level === 'low').length,
  };

  const visible = filter === 'all' ? alerts : alerts.filter((a) => a.level === filter);

  if (!open) {
    return (
      <button className="haz-toggle" onClick={() => setOpen(true)}>
        ☰ ALERTS
      </button>
    );
  }

  return (
    <div className="haz-panel">
      <div className="haz-panel-head">
        ALERT LIST&nbsp;({alerts.length})
        <span className="haz-panel-close" onClick={() => setOpen(false)}>×</span>
      </div>

      <div className="haz-filters">
        <button className={filter === 'all' ? 'active' : ''} onClick={() => setFilter('all')}>
          All
        </button>
        <button className={filter === 'high' ? 'active' : ''} onClick={() => setFilter('high')}>
          Red {counts.high}
        </button>
        <button className={filter === 'medium' ? 'active' : ''} onClick={() => setFilter('medium')}>
          Orange {counts.medium}
        </button>
        <button className={filter === 'low' ? 'active' : ''} onClick={() => setFilter('low')}>
          Yellow {counts.low}
        </button>
      </div>

      <div className="haz-list">
        {visible.length === 0 && (
          <div className="haz-empty">No alerts at this level.</div>
        )}

        {visible.map((a, i) => {
          const c = LEVEL_COLORS[a.level];
          const meta = HAZARD_META[a.hazard];
          return (
            <div
              key={`${a.nodeId}-${a.hazard}-${i}`}
              className="haz-card"
              style={{ background: c.bg, color: c.fg }}
              onClick={() => onFocusAlert?.(a)}
            >
              <b>{meta.icon} {meta.label} — {c.name.toUpperCase()}</b>
              {a.place}
              <small>{a.reason}</small>
            </div>
          );
        })}
      </div>
    </div>
  );
}
