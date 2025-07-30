import { PolygonWithRoute, Vertex } from "@/types/cityeye/cityEyePolygon";

export const POLYGON_CONFIG = {
  MAX_POLYGONS: 8,
  MAX_NAME_LENGTH: 10,
  DEFAULT_VERTICES_COUNT: 4,
  IMAGE_DIMENSIONS: {
    DISPLAY: { width: 1000, height: 563 },
    ACTUAL: { width: 1280, height: 720 },
  },
  COLORS: {
    PRIMARY: "#7048ec",
    PRIMARY_ALPHA: "#7048ec7f",
  },
  DEFAULT_MAP_CENTER: { lat: 36.5287, lng: 139.8147 },
  DEFAULT_MAP_ZOOM: 16,
  CAPTURE_TIMEOUT_MS: 30000,
} as const;

export const LEAFLET_CONFIG = {
  iconRetinaUrl: "/images/media/marker-icon-2x.png",
  iconUrl: "/images/media/marker-icon.png",
  shadowUrl: "/images/media/marker-shadow.png",
} as const;

export const TILE_LAYERS = {
  OSM: {
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
  },
  GSI: {
    attribution:
      '&copy; <a href="https://maps.gsi.go.jp/development/ichiran.html">国土地理院</a>',
    url: "https://cyberjapandata.gsi.go.jp/xyz/std/{z}/{x}/{y}.png",
  },
} as const;

// Utility function for coordinate conversion
export const convertPosition = ({
  position,
  inputWidth,
  inputHeight,
  targetWidth,
  targetHeight,
}: {
  position: { x: number; y: number };
  inputWidth: number;
  inputHeight: number;
  targetWidth: number;
  targetHeight: number;
}) => {
  return {
    x: Math.round((position.x / inputWidth) * targetWidth),
    y: Math.round((position.y / inputHeight) * targetHeight),
  };
};

// Convert display coordinates to actual coordinates
export const displayToActual = (position: { x: number; y: number }) => {
  return convertPosition({
    position,
    inputWidth: POLYGON_CONFIG.IMAGE_DIMENSIONS.DISPLAY.width,
    inputHeight: POLYGON_CONFIG.IMAGE_DIMENSIONS.DISPLAY.height,
    targetWidth: POLYGON_CONFIG.IMAGE_DIMENSIONS.ACTUAL.width,
    targetHeight: POLYGON_CONFIG.IMAGE_DIMENSIONS.ACTUAL.height,
  });
};

// Convert actual coordinates to display coordinates
export const actualToDisplay = (position: { x: number; y: number }) => {
  return convertPosition({
    position,
    inputWidth: POLYGON_CONFIG.IMAGE_DIMENSIONS.ACTUAL.width,
    inputHeight: POLYGON_CONFIG.IMAGE_DIMENSIONS.ACTUAL.height,
    targetWidth: POLYGON_CONFIG.IMAGE_DIMENSIONS.DISPLAY.width,
    targetHeight: POLYGON_CONFIG.IMAGE_DIMENSIONS.DISPLAY.height,
  });
};

// Generate a new polygon ID based on existing ones
export const generateNewPolygonId = (
  existingPolygons: PolygonWithRoute[]
): string => {
  const existingIds = existingPolygons
    .map((p) => parseInt(p.polygonId, 10))
    .sort((a, b) => a - b);
  const newId = existingIds.reduce(
    (acc, cur) => (acc === cur ? acc + 1 : acc),
    1
  );
  return newId.toString();
};

// Create default vertices for a new polygon
export const createDefaultVertices = (polygonId: string): Vertex[] => {
  return [
    { vertexId: `${polygonId}-1`, position: { x: 10, y: 10 } },
    { vertexId: `${polygonId}-2`, position: { x: 200, y: 10 } },
    { vertexId: `${polygonId}-3`, position: { x: 200, y: 200 } },
    { vertexId: `${polygonId}-4`, position: { x: 10, y: 200 } },
  ];
};
