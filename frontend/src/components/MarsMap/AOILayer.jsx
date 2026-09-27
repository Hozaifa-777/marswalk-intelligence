import { Rectangle, Tooltip } from "react-leaflet";

import { MARS_MAP } from "../../utils/mapConfig";

const AOI_BOUNDS = [
  [MARS_MAP.bounds.minY, MARS_MAP.bounds.minX],
  [MARS_MAP.bounds.maxY, MARS_MAP.bounds.maxX],
];

function AOILayer() {
  return (
    <Rectangle
      bounds={AOI_BOUNDS}
      pathOptions={{
        color: "#4fc3f7",
        weight: 2,
        dashArray: "6 6",
        fillOpacity: 0.03,
      }}
    >
      <Tooltip sticky>Jezero Operational Sector — 10 × 10 km AOI</Tooltip>
    </Rectangle>
  );
}

export default AOILayer;
