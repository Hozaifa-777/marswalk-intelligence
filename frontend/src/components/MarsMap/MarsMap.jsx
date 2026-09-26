import { useEffect } from "react";

import {
  MapContainer,
  TileLayer,
  CircleMarker,
  useMap,
} from "react-leaflet";

import "leaflet/dist/leaflet.css";

import { MarsCRS } from "../../utils/marsCRS";

const CTX_BOUNDS = [
  [1042131.6352, 4329192.1081],
  [1143347.4242, 4418058.7893],
];

const TEST_POINT = [
  1099980.91,
  4357354.05,
];

/**
 * Fit the map to the complete CTX coverage.
 */
function FitCTX() {
  const map = useMap();

  useEffect(() => {
    map.fitBounds(CTX_BOUNDS, {
      padding: [0, 0],
      animate: false,
    });
    map.setMinZoom(map.getZoom());
  }, [map]);

  return null;
}

function MarsMap() {
  return (
    <MapContainer
      crs={MarsCRS}
      center={[1095000, 4355000]}
      zoom={4}
      zoomSnap={0.25} 

      /*
       * z=0 is allowed technically,
       * but we don't want the raster
       * to become smaller than the viewport.
       *
       * z=1 gives us a safer minimum
       * while we establish the final UI.
       */
      minZoom={1}
      maxZoom={7}

      maxBounds={CTX_BOUNDS}
      maxBoundsViscosity={1.0}

      zoomControl={true}

      style={{
        width: "100vw",
        height: "100vh",
        background: "#000",
      }}
    >
      <FitCTX />

      <TileLayer
        url="/tiles/ctx/{z}/{x}/{y}.png"
        tileSize={256}
        minZoom={1}
        maxNativeZoom={7}   
        maxZoom={7}
        attribution="NASA / MarsWalk Intelligence"
        noWrap={true}
      />

      {/* Temporary coordinate alignment test */}
      <CircleMarker
        center={TEST_POINT}
        radius={8}
        pathOptions={{
          color: "red",
          fillColor: "red",
          fillOpacity: 1,
          weight: 2,
        }}
      />
    </MapContainer>
  );
}

export default MarsMap;