import React from 'react';
export default function LocationCard({node}){return <div className="location-card">
 <div className="pin-dot">●</div><div><div className="eyebrow">SELECTED MONITORING NODE</div><h2>{node.name}</h2>
 {node.radiusKm && <div className="meta">Radius <b>{node.radiusKm} km</b> · {node.lat.toFixed(4)}°N, {node.lng.toFixed(4)}°E</div>}
 {node.cities && <div className="cities">{node.cities.join(' · ')}</div>}
 <div className="state">Tamil Nadu · IST</div></div></div>}
