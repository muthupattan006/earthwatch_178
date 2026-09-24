import React, { useMemo, useState } from 'react';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { NODES } from './data';
import Dashboard from './pages/Dashboard';
import Forecast from './pages/Forecast';
import Nowcast from './pages/Nowcast';
import Historical from './pages/Historical';
import logo from './EarthWatch_logo.png';

export default function App(){
  const [nodeId,setNodeId] = useState('PAN-01');
  const node = useMemo(()=>NODES.find(n=>n.id===nodeId) ?? NODES[0],[nodeId]);
  return <div className="app-shell">
    <Header node={node} nodeId={nodeId} setNodeId={setNodeId}/>
    <Routes>
      <Route path="/" element={<Dashboard node={node} setNodeId={setNodeId}/>}/>
      <Route path="/forecast" element={<Forecast node={node}/>}/>
      <Route path="/nowcast" element={<Nowcast node={node}/>}/>
      <Route path="/historical" element={<Historical node={node}/>}/>
    </Routes>
  </div>
}

function Header({ node, nodeId, setNodeId }) {
  const nav = useNavigate();
  const loc = useLocation();

  return (
    <header className="topbar">

      <div
        className="brand"
        onClick={() => nav('/')}
        style={{ cursor: 'pointer' }}
      >
        <img src={logo} alt="Earthwatch logo" className="brand-mark" />

        <div>
          <b>EARTHWATCH</b>
          <span>Multi-Hazard Monitoring</span>
        </div>
      </div>


      {/* Node selector */}
      <select
        value={nodeId}
        onChange={(e) => {
          setNodeId(e.target.value);
          nav('/');
        }}
        className="node-select"
      >
        {NODES.map(n => (
          <option
            key={n.id}
            value={n.id}
          >
            {n.name}
          </option>
        ))}
      </select>


      {/* Only MAP remains in the top navigation */}
      <div className="nav-tabs">
        <button
          className={loc.pathname === '/' ? 'active' : ''}
          onClick={() => nav('/')}
        >
          MAP
        </button>
      </div>


      <div className="status">
        <i />
        LIVE NODE: {node.name.toUpperCase()}
      </div>

    </header>
  );
}
