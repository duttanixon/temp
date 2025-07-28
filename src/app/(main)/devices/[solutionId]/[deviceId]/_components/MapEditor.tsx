import {
  Point,
  PolygonStates,
  PolygonWithRoute,
} from "@/types/cityeye/cityEyePolygon";
import {
  POLYGON_CONFIG,
  TILE_LAYERS,
} from "@/utils/analytics/city_eye/polygon.utils";
import React from "react";
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
}

// Component for the map editor view
export const MapEditor: React.FC<MapEditorProps> = ({
  polygons,
  polygonsState,
  isOsm,
  onToggleMap,
  onUpdateRouteMarker,
}) => {
  const tileLayer = isOsm ? TILE_LAYERS.OSM : TILE_LAYERS.GSI;

  console.log("MapEditor polygons:", polygons);
  console.log("MapEditor polygonsState:", polygonsState);
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
      <MapContainer
        center={
          polygons.length > 0
            ? polygons[0].center.startPoint
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
                positions={[polygon.center.startPoint, polygon.center.endPoint]}
              />
            </React.Fragment>
          ) : null
        )}
      </MapContainer>
    </div>
  );
};
