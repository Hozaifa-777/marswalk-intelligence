
import { useEffect, useMemo, useState } from "react";

import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";

import * as THREE from "three";

import "./Terrain3D.css";


const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

const VERTICAL_EXAGGERATION = 2;


function getFiniteRange(values) {
  let min = Infinity;
  let max = -Infinity;

  for (const value of values) {
    if (!Number.isFinite(value)) continue;

    if (value < min) min = value;
    if (value > max) max = value;
  }

  return { min, max };
}


// ============================================================
// TERRAIN GEOMETRY
// ============================================================

function buildTerrainGeometry(
  data,
  verticalExaggeration = VERTICAL_EXAGGERATION
) {

  const rows = data.height;
  const cols = data.width;

  const elevations = data.elevation_m;
  const slopes = data.slope_deg;
  const validMask = data.valid_mask;

  const rowIndices = data.row_indices;
  const colIndices = data.col_indices;

  const transform = data.transform;

  if (
    !Number.isInteger(rows) ||
    !Number.isInteger(cols) ||
    rows < 2 ||
    cols < 2 ||

    !Array.isArray(elevations) ||
    elevations.length !== rows ||

    !Array.isArray(slopes) ||
    slopes.length !== rows ||

    !Array.isArray(validMask) ||
    validMask.length !== rows ||

    !Array.isArray(rowIndices) ||
    rowIndices.length !== rows ||

    !Array.isArray(colIndices) ||
    colIndices.length !== cols ||

    !Array.isArray(transform) ||
    transform.length < 6
  ) {
    throw new Error(
      "Heightmap dimensions or coordinate metadata are invalid."
    );
  }

  const [a, b, c, d, e, f] = transform;

  const elevationRangeValues = [];

  let minSlope = Infinity;
  let maxSlope = -Infinity;

  for (let row = 0; row < rows; row++) {

    if (
      elevations[row]?.length !== cols ||
      slopes[row]?.length !== cols ||
      validMask[row]?.length !== cols
    ) {
      throw new Error(
        "Heightmap rows have inconsistent dimensions."
      );
    }

    for (let col = 0; col < cols; col++) {

      const elevation = elevations[row][col];
      const slope = slopes[row][col];

      if (
        validMask[row][col] &&
        Number.isFinite(elevation)
      ) {
        elevationRangeValues.push(elevation);
      }

      if (
        validMask[row][col] &&
        Number.isFinite(slope)
      ) {
        minSlope = Math.min(minSlope, slope);
        maxSlope = Math.max(maxSlope, slope);
      }
    }
  }

  const {
    min: minElevation,
    max: maxElevation,
  } = getFiniteRange(elevationRangeValues);

  if (
    !Number.isFinite(minElevation) ||
    !Number.isFinite(maxElevation)
  ) {
    throw new Error(
      "Heightmap contains no valid elevation samples."
    );
  }

  if (!Number.isFinite(minSlope)) minSlope = 0;
  if (!Number.isFinite(maxSlope)) maxSlope = 0;

  const elevationRange = Math.max(
    maxElevation - minElevation,
    1
  );

  const xCoordinates = [];
  const yCoordinates = [];

  for (let col = 0; col < cols; col++) {

    const sourceCol = colIndices[col] + 0.5;
    const sourceRow = rowIndices[0] + 0.5;

    xCoordinates.push(
      a * sourceCol +
      b * sourceRow +
      c
    );
  }

  for (let row = 0; row < rows; row++) {

    const sourceCol = colIndices[0] + 0.5;
    const sourceRow = rowIndices[row] + 0.5;

    yCoordinates.push(
      d * sourceCol +
      e * sourceRow +
      f
    );
  }

  if (
    Math.abs(b) > 1e-9 ||
    Math.abs(d) > 1e-9
  ) {
    throw new Error(
      "Rotated DEM transforms are not supported."
    );
  }

  const xMin = Math.min(...xCoordinates);
  const xMax = Math.max(...xCoordinates);

  const yMin = Math.min(...yCoordinates);
  const yMax = Math.max(...yCoordinates);

  const horizontalScale =
    100 / Math.max(
      xMax - xMin,
      yMax - yMin,
      1
    );

  const positions = [];
  const colors = [];
  const uvs = [];
  const indices = [];

  const color = new THREE.Color();

  const fallbackLow = new THREE.Color("#765b43");
  const fallbackMid = new THREE.Color("#b58b55");
  const fallbackHigh = new THREE.Color("#d9c7a0");
  const invalidColor = new THREE.Color("#252b2e");

  for (let row = 0; row < rows; row++) {

    for (let col = 0; col < cols; col++) {

      const elevation = elevations[row][col];
      const slope = slopes[row][col];

      const isValid =
        Boolean(validMask[row][col]) &&
        Number.isFinite(elevation) &&
        Number.isFinite(slope);

      const x =
        (xCoordinates[col] - (xMin + xMax) / 2) *
        horizontalScale;

      const z =
        -(
          (yCoordinates[row] - (yMin + yMax) / 2) *
          horizontalScale
        );

      const y = isValid
        ? (
            (elevation - minElevation) /
            elevationRange
          ) * 12 * verticalExaggeration
        : 0;

      positions.push(x, y, z);

      // CTX texture UV mapping.
      // Row 0 represents the northern/top edge of the raster.
      uvs.push(
        col / (cols - 1),
        1 - row / (rows - 1)
      );

      // Keep slope visualization as fallback.
      const slopeRatio = isValid
        ? THREE.MathUtils.clamp(slope / 25, 0, 1)
        : 0;

      if (slopeRatio < 0.5) {

        color
          .copy(fallbackLow)
          .lerp(
            fallbackMid,
            slopeRatio * 2
          );

      } else {

        color
          .copy(fallbackMid)
          .lerp(
            fallbackHigh,
            (slopeRatio - 0.5) * 2
          );
      }

      if (!isValid) {
        color.copy(invalidColor);
      }

      colors.push(
        color.r,
        color.g,
        color.b
      );
    }
  }

  // Generate triangles only when all four vertices are valid.
  for (let row = 0; row < rows - 1; row++) {

    for (let col = 0; col < cols - 1; col++) {

      const i = row * cols + col;

      const corners = [
        i,
        i + 1,
        i + cols,
        i + cols + 1,
      ];

      const allValid = corners.every((index) => {

        const r = Math.floor(index / cols);
        const column = index % cols;

        return (
          Boolean(validMask[r][column]) &&
          Number.isFinite(elevations[r][column]) &&
          Number.isFinite(slopes[r][column])
        );
      });

      if (allValid) {

        indices.push(
          i,
          i + cols,
          i + 1,

          i + 1,
          i + cols,
          i + cols + 1
        );
      }
    }
  }

  const geometry = new THREE.BufferGeometry();

  geometry.setAttribute(
    "position",
    new THREE.Float32BufferAttribute(
      positions,
      3
    )
  );

  geometry.setAttribute(
    "color",
    new THREE.Float32BufferAttribute(
      colors,
      3
    )
  );

  geometry.setAttribute(
    "uv",
    new THREE.Float32BufferAttribute(
      uvs,
      2
    )
  );

  geometry.setIndex(indices);

  geometry.computeVertexNormals();

  return {
    geometry,

    stats: {
      minElevation,
      maxElevation,
      minSlope,
      maxSlope,

      widthMeters: xMax - xMin,
      heightMeters: yMax - yMin,
    },
  };
}


// ============================================================
// CTX TEXTURE LOADER
// ============================================================

function useCTXTexture() {

  const [texture, setTexture] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {

    let active = true;
    let loadedTexture = null;

    const loader = new THREE.TextureLoader();

    loader.load(
      `${API_BASE}/api/v1/terrain/texture?v=2`,

      (result) => {

        if (!active) {
          result.dispose();
          return;
        }

        loadedTexture = result;

        result.colorSpace = THREE.SRGBColorSpace;

        result.wrapS = THREE.ClampToEdgeWrapping;
        result.wrapT = THREE.ClampToEdgeWrapping;

        result.magFilter = THREE.LinearFilter;

        result.minFilter =
          THREE.LinearMipmapLinearFilter;

        result.generateMipmaps = true;

        result.needsUpdate = true;

        setTexture(result);
      },

      undefined,

      (loadError) => {

        if (active) {
          setError(
            loadError?.message ||
            "CTX texture could not be loaded."
          );
        }
      }
    );

    return () => {

      active = false;

      if (loadedTexture) {
        loadedTexture.dispose();
      }
    };

  }, []);

  return {
    texture,
    error,
  };
}


// ============================================================
// TERRAIN MESH
// ============================================================

function TerrainMesh({ data, texture }) {

  const terrain = useMemo(
    () => buildTerrainGeometry(data),
    [data]
  );

  useEffect(() => {

    return () => {
      terrain.geometry.dispose();
    };

  }, [terrain]);

  return (
    <mesh
      geometry={terrain.geometry}
      receiveShadow
      castShadow
    >

      <meshStandardMaterial
        map={texture || null}
        vertexColors={!texture}
        color="#ffffff"
        roughness={0.95}
        metalness={0}
        side={THREE.DoubleSide}
      />

    </mesh>
  );
}


// ============================================================
// THREE.JS SCENE
// ============================================================


function Scene({ data, texture }) {
  return (
    <>
      <color
        attach="background"
        args={["#101416"]}
      />

      {/* Soft environmental lighting */}
      <hemisphereLight
        args={["#dce7ee", "#49372b", 0.9]}
      />

      <ambientLight intensity={0.35} />

      {/* Directional sunlight */}
      <directionalLight
        position={[-45, 70, 35]}
        intensity={1.7}
        castShadow
        shadow-mapSize-width={1024}
        shadow-mapSize-height={1024}
        shadow-camera-left={-70}
        shadow-camera-right={70}
        shadow-camera-top={70}
        shadow-camera-bottom={-70}
        shadow-camera-near={1}
        shadow-camera-far={180}
        shadow-bias={-0.00015}
        shadow-normalBias={0.02}
      />

      <TerrainMesh
        data={data}
        texture={texture}
      />

      <gridHelper
        args={[
          120,
          12,
          "#394247",
          "#222a2e",
        ]}
        position={[0, -0.8, 0]}
      />

      <OrbitControls
        makeDefault
        enableDamping
        dampingFactor={0.08}
        minDistance={18}
        maxDistance={180}
        maxPolarAngle={Math.PI * 0.49}
        target={[0, 3, 0]}
      />
    </>
  );
}


// ============================================================
// MAIN COMPONENT
// ============================================================

export default function Terrain3D() {

  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const {
    texture,
    error: textureError,
  } = useCTXTexture();


  useEffect(() => {

    const controller = new AbortController();

    async function loadTerrain() {

      try {

        setLoading(true);
        setError("");

        const response = await fetch(
          `${API_BASE}/api/v1/terrain/heightmap?max_dimension=256`,
          {
            signal: controller.signal,
          }
        );

        if (!response.ok) {

          const detail = await response.text();

          throw new Error(
            `Terrain API ${response.status}: ${detail}`
          );
        }

        const payload = await response.json();

        if (
          !payload.elevation_m ||
          !payload.slope_deg ||
          !payload.valid_mask ||
          !payload.row_indices ||
          !payload.col_indices ||
          !payload.transform
        ) {
          throw new Error(
            "Terrain API response is missing required fields."
          );
        }

        setData(payload);

      } catch (err) {

        if (err.name !== "AbortError") {

          setError(
            err.message ||
            "Could not load terrain."
          );
        }

      } finally {

        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    loadTerrain();

    return () => controller.abort();

  }, []);


  if (loading) {

    return (
      <div className="terrain3d-state">
        LOADING JEZERO ELEVATION MODEL…
      </div>
    );
  }


  if (error) {

    return (
      <div className="terrain3d-state terrain3d-state--error">
        3D TERRAIN UNAVAILABLE · {error}
      </div>
    );
  }


  const elevations = data.elevation_m.flat();
  const slopes = data.slope_deg.flat();

  const {
    min: minElevation,
    max: maxElevation,
  } = getFiniteRange(elevations);

  const {
    max: maxSlope,
  } = getFiniteRange(slopes);


  return (

    <div className="terrain3d">

      <Canvas
          shadows
          camera={{
            position: [72, 58, 82],
            fov: 42,
            near: 0.1,
            far: 500,
          }}
          dpr={[1, 1.5]}
           >        

        <Scene
          data={data}
          texture={texture}
        />

      </Canvas>


      <div className="terrain3d__legend">

        <strong>
          JEZERO · 3D TERRAIN
        </strong>

        <span>
          DEM {data.source_width} × {data.source_height}
          {" · "}
          DISPLAY {data.width} × {data.height}
        </span>

        <span>
          ELEVATION {minElevation.toFixed(1)}
          {" → "}
          {maxElevation.toFixed(1)} m
        </span>

        <span>
          MAX SLOPE{" "}
          {(Number.isFinite(maxSlope) ? maxSlope : 0).toFixed(1)}
          °
          {" · "}
          VERTICAL EXAGGERATION {VERTICAL_EXAGGERATION}×
        </span>

        <span>
          {texture
            ? "CTX ORTHOMOSAIC TEXTURE READY"
            : textureError
              ? `CTX TEXTURE ERROR · ${textureError}`
              : "LOADING CTX TEXTURE..."}
        </span>

        <span>
          DRAG TO ORBIT · SCROLL TO ZOOM
        </span>

      </div>

    </div>
  );
}
