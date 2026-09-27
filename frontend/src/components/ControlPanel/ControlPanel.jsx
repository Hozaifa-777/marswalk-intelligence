function LayerToggle({ label, checked, onChange, disabled }) {
  return (
    <label
      className={
        "layer-toggle" + (disabled ? " layer-toggle--disabled" : "")
      }
    >
      <input
        type="checkbox"
        checked={checked}
        disabled={disabled}
        onChange={(event) => onChange && onChange(event.target.checked)}
      />
      {label}
    </label>
  );
}

function ControlPanel({ layers, onToggleLayer }) {
  return (
    <aside className="control-panel">
      <section className="control-panel__section">
        <h3>Base Map</h3>
        <LayerToggle
          label="CTX Orthomosaic"
          checked={layers.ctx}
          onChange={(value) => onToggleLayer("ctx", value)}
        />
      </section>

      <section className="control-panel__section">
        <h3>Navigation</h3>
        <LayerToggle
          label="AOI Boundary"
          checked={layers.aoi}
          onChange={(value) => onToggleLayer("aoi", value)}
        />
        <LayerToggle label="Route" checked={false} disabled />
      </section>

      <section className="control-panel__section">
        <h3>Terrain</h3>
        <LayerToggle label="DEM" checked={false} disabled />
        <LayerToggle label="Slope" checked={false} disabled />
      </section>

      <section className="control-panel__section">
        <h3>Science</h3>
        <LayerToggle label="CRISM" checked={false} disabled />
        <LayerToggle label="Science Targets" checked={false} disabled />
      </section>
    </aside>
  );
}

export default ControlPanel;
