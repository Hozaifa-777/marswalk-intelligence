import { useState } from "react";

import HUD from "./components/HUD/HUD";
import ControlPanel from "./components/ControlPanel/ControlPanel";
import MarsMap from "./components/MarsMap/MarsMap";

import "./App.css";

function App() {
  const [layers, setLayers] = useState({
    ctx: true,
    aoi: true,
  });

  const handleToggleLayer = (key, value) => {
    setLayers((previous) => ({ ...previous, [key]: value }));
  };

  return (
    <div className="app-shell">
      <HUD />

      <div className="app-body">
        <ControlPanel layers={layers} onToggleLayer={handleToggleLayer} />

        <main className="app-map">
          <MarsMap layers={layers} />
        </main>
      </div>
    </div>
  );
}

export default App;
