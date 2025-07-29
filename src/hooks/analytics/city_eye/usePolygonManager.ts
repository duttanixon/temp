import {
  PolygonStates,
  PolygonWithRoute,
} from "@/types/cityeye/cityEyePolygon";
import {
  createDefaultVertices,
  generateNewPolygonId,
  POLYGON_CONFIG,
} from "@/utils/analytics/city_eye/polygon.utils";
import { useCallback, useState } from "react";

// Custom hook for managing polygon state
export const usePolygonManager = ({
  latitude,
  longitude,
}: {
  latitude: number;
  longitude: number;
}) => {
  const [polygons, setPolygons] = useState<PolygonWithRoute[]>([]);
  const [polygonsState, setPolygonsState] = useState<PolygonStates>({});

  const togglePolygonVisibility = useCallback((id: string) => {
    setPolygonsState((prev) => ({
      ...prev,
      [id]: {
        ...prev[id],
        visible: !prev[id].visible,
      },
    }));
  }, []);

  const togglePolygonActiveState = useCallback((selectedId: string) => {
    setPolygonsState((previousState) => {
      const updatedState = { ...previousState };
      Object.keys(updatedState).forEach((id) => {
        updatedState[id] = {
          ...updatedState[id],
          active: id === selectedId ? !updatedState[id].active : false,
        };
      });
      return updatedState;
    });
  }, []);

  const addPolygon = useCallback(() => {
    if (polygons.length >= POLYGON_CONFIG.MAX_POLYGONS) return;

    const newPolygonId = generateNewPolygonId(polygons);
    const newPolygon: PolygonWithRoute = {
      polygonId: newPolygonId,
      name: `New Zone ${newPolygonId}`,
      vertices: createDefaultVertices(newPolygonId),
      center: {
        startPoint: { lat: latitude, lng: longitude },
        endPoint: {
          lat: latitude - 0.0002,
          lng: longitude - 0.0003,
        },
      },
    };

    setPolygons((prev) => [...prev, newPolygon]);
    setPolygonsState((prev) => ({
      ...prev,
      [newPolygonId]: { visible: true, active: true },
    }));
  }, [polygons, latitude, longitude]);

  const removePolygon = useCallback(
    (index: number) => {
      const polygonId = polygons[index].polygonId;
      setPolygons((prev) => prev.filter((_, i) => i !== index));
      setPolygonsState((prev) => {
        const newState = { ...prev };
        delete newState[polygonId];
        return newState;
      });
    },
    [polygons]
  );

  const updatePolygonName = useCallback((index: number, name: string) => {
    setPolygons((prev) =>
      prev.map((poly, i) => (i === index ? { ...poly, name } : poly))
    );
  }, []);

  const updatePolygonVertices = useCallback(
    (activeId: string, deltaX: number, deltaY: number) => {
      setPolygons((prevPolygons) =>
        prevPolygons.map((poly) => ({
          ...poly,
          vertices: poly.vertices.map((vertex) =>
            vertex.vertexId === activeId
              ? {
                  ...vertex,
                  position: {
                    x: Math.round(vertex.position.x + deltaX),
                    y: Math.round(vertex.position.y + deltaY),
                  },
                }
              : vertex
          ),
        }))
      );
    },
    []
  );

  const updateRouteMarker = useCallback(
    (
      polygonId: string,
      point: "start" | "end",
      position: { lat: number; lng: number }
    ) => {
      setPolygons((prev) =>
        prev.map((poly) =>
          poly.polygonId === polygonId
            ? {
                ...poly,
                center: {
                  ...poly.center,
                  [point === "start" ? "startPoint" : "endPoint"]: position,
                },
              }
            : poly
        )
      );
    },
    []
  );

  return {
    polygons,
    setPolygons,
    polygonsState,
    setPolygonsState,
    togglePolygonVisibility,
    togglePolygonActiveState,
    addPolygon,
    removePolygon,
    updatePolygonName,
    updatePolygonVertices,
    updateRouteMarker,
  };
};
