import L from "leaflet";

const CTX_ORIGIN_X = 4329192.10812596;
const CTX_ORIGIN_Y = 1143347.424174998;

const CTX_RES_X = 5.002064681102627;
const CTX_RES_Y = 5.002262971613293;

const CTX_WIDTH = 17766;
const CTX_HEIGHT = 20234;

const TILE_SIZE = 256;
const MAX_ZOOM = 7;

const TILE_MATRIX_WIDTH = 70 * TILE_SIZE;
const TILE_MATRIX_HEIGHT = 80 * TILE_SIZE;

/**
 * Mars projected coordinates -> CTX native raster pixels
 */
function marsToPixel(point) {
  return L.point(
    (point.x - CTX_ORIGIN_X) / CTX_RES_X,
    (CTX_ORIGIN_Y - point.y) / CTX_RES_Y
  );
}

/**
 * CTX native raster pixels -> Mars projected coordinates
 */
function pixelToMars(point) {
  return L.point(
    CTX_ORIGIN_X + point.x * CTX_RES_X,
    CTX_ORIGIN_Y - point.y * CTX_RES_Y
  );
}

const MarsProjection = {
  project(latlng) {
    return marsToPixel({
      x: latlng.lng,
      y: latlng.lat,
    });
  },

  unproject(point) {
    const mars = pixelToMars(point);

    return L.latLng(
      mars.y,
      mars.x
    );
  },

  bounds: L.bounds(
    [0, 0],
    [TILE_MATRIX_WIDTH, TILE_MATRIX_HEIGHT]
  ),
};

export const MarsCRS = L.extend({}, L.CRS, {
  code: "MARS_CTX",

  projection: MarsProjection,

  transformation: new L.Transformation(
    1,
    0,
    1,
    0
  ),

  /**
   * Native CTX resolution is z=7.
   *
   * z=7 -> 1x
   * z=6 -> 1/2
   * z=5 -> 1/4
   * ...
   */
  scale(zoom) {
    return 2 ** (zoom - MAX_ZOOM);
  },

  zoom(scale) {
    return Math.log2(scale) + MAX_ZOOM;
  },

  distance(latlng1, latlng2) {
    const dx = latlng2.lng - latlng1.lng;
    const dy = latlng2.lat - latlng1.lat;

    return Math.sqrt(
      dx * dx + dy * dy
    );
  },

  infinite: false,
});

export {
  CTX_ORIGIN_X,
  CTX_ORIGIN_Y,
  CTX_RES_X,
  CTX_RES_Y,
  CTX_WIDTH,
  CTX_HEIGHT,
  TILE_SIZE,
  MAX_ZOOM,
  TILE_MATRIX_WIDTH,
  TILE_MATRIX_HEIGHT,
  marsToPixel,
  pixelToMars,
};