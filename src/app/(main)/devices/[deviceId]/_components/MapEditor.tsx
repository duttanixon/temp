import { Button } from "@/components/ui/button";
import {
  Point,
  PolygonStates,
  PolygonWithRoute,
} from "@/types/cityeye/cityEyePolygon";
import {
  POLYGON_CONFIG,
  TILE_LAYERS,
} from "@/utils/analytics/city_eye/polygon.utils";
import { RefreshCcw } from "lucide-react";
import React, { useCallback, useState } from "react";
import { MapContainer, TileLayer } from "react-leaflet";
import { DraggableMapMarker } from "./DraggableMapMarker";
import { PolylineArrow } from "./PolylineArrow";
import { ToggleButton } from "./ToggleButton";

interface MapEditorProps {
  polygons: PolygonWithRoute[];
  polygonsState: PolygonStates;
  isOsm: boolean;
  onToggleMap: (isOsm: boolean) => void;
  onUpdateRouteMarker: (
    polygonId: string,
    point: "start" | "end",
    position: Point
  ) => void;
  latitude?: number;
  longitude?: number;
}

const ResetButton = ({ onClick }: { onClick: () => void }) => {
  return (
    <Button
      size="sm"
      className="cursor-pointer text-xs bg-white hover:bg-gray-50 text-gray-700 border border-gray-300 shadow-md"
      onClick={onClick}
    >
      <RefreshCcw />
    </Button>
  );
};

// Component for the map editor view
export const MapEditor: React.FC<MapEditorProps> = ({
  polygons,
  polygonsState,
  isOsm,
  onToggleMap,
  onUpdateRouteMarker,
  latitude,
  longitude,
}) => {
  const tileLayer = isOsm ? TILE_LAYERS.OSM : TILE_LAYERS.GSI;
  const [resetKey, setResetKey] = useState(0);
  const handleReset = useCallback(() => {
    setResetKey((k) => k + 1);
  }, [setResetKey]);

  return (
    <div className="w-[1000px]">
      <div className="mb-4">
        <ToggleButton
          checked={isOsm}
          onChange={onToggleMap}
          uncheckedLabel="地理院地図"
          checkedLabel="OSM"
        />
      </div>
      <div className="w-full h-120 relative z-[1]">
        <div className="absolute top-20 left-2 z-[1000]">
          <ResetButton onClick={handleReset} />
        </div>
        <MapContainer
          key={resetKey}
          center={
            latitude != null && longitude != null
              ? { lat: latitude, lng: longitude }
              : POLYGON_CONFIG.DEFAULT_MAP_CENTER
          }
          zoom={POLYGON_CONFIG.DEFAULT_MAP_ZOOM}
          style={{ height: "500px", width: "100%" }}
        >
          <TileLayer attribution={tileLayer.attribution} url={tileLayer.url} />
          {polygons.map((polygon) =>
            polygonsState[polygon.polygonId]?.visible ? (
              <React.Fragment key={polygon.polygonId}>
                {polygonsState[polygon.polygonId]?.active && (
                  <>
                    <DraggableMapMarker
                      position={polygon.center.startPoint}
                      onDrag={(pos) =>
                        onUpdateRouteMarker(polygon.polygonId, "start", pos)
                      }
                      label="Start"
                    />
                    <DraggableMapMarker
                      position={polygon.center.endPoint}
                      onDrag={(pos) =>
                        onUpdateRouteMarker(polygon.polygonId, "end", pos)
                      }
                      label="End"
                    />
                  </>
                )}
                <PolylineArrow
                  positions={[
                    polygon.center.startPoint,
                    polygon.center.endPoint,
                  ]}
                />
              </React.Fragment>
            ) : null
          )}
        </MapContainer>
      </div>
    </div>
  );
};
