import { useState, useCallback } from 'react';
import { toast } from 'sonner';
import { polygonService } from '@/services/cityeye/cityEyePolygonSettings';
import { XLinesConfigPayload } from '@/types/cityeye/cityEyePolygon';
import { PolygonWithRoute, PolygonStates } from '@/types/cityeye/cityEyePolygon';
import { actualToDisplay, displayToActual } from '@/utils/analytics/city_eye/polygon.utils';

// Custom hook for polygon configuration loading and saving
export const usePolygonConfig = (
  deviceId: string,
  setPolygons: (polygons: PolygonWithRoute[]) => void,
  setPolygonsState: (states: PolygonStates) => void
) => {
  const [isLoadingConfig, setIsLoadingConfig] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  const loadPolygonConfig = useCallback(async () => {
    try {
      setIsLoadingConfig(true);
      const config = await polygonService.getPolygonConfig(deviceId);
      
      if (config && config.detectionZones && config.detectionZones.length > 0) {
        // Convert from backend format to frontend format
        const loadedPolygons: PolygonWithRoute[] = config.detectionZones.map((zone) => ({
          polygonId: zone.polygonId,
          name: zone.name,
          vertices: zone.vertices.map((v) => ({
            vertexId: v.vertexId,
            position: actualToDisplay(v.position),
          })),
          center: zone.center,
        }));

        setPolygons(loadedPolygons);
        
        const newState: PolygonStates = {};
        loadedPolygons.forEach((poly) => {
          newState[poly.polygonId] = { visible: true, active: false };
        });
        setPolygonsState(newState);
        
        toast.success("Polygon configuration loaded successfully");
      }
    } catch (error) {
      console.error("Failed to load polygon config:", error);
      // Don't show error toast for 404, just start with empty polygons
      if (error instanceof Error && !error.message.includes("404")) {
        toast.error("Failed to load polygon configuration");
      }
    } finally {
      setIsLoadingConfig(false);
    }
  }, [deviceId, setPolygons, setPolygonsState]);

  const savePolygonConfig = useCallback(async (polygons: PolygonWithRoute[]) => {
    try {
      setIsSaving(true);

      const payload: XLinesConfigPayload = {
        device_id: deviceId,
        detectionZones: polygons.map((poly) => ({
          polygonId: poly.polygonId,
          name: poly.name,
          vertices: poly.vertices.map((v) => ({
            vertexId: v.vertexId,
            position: displayToActual(v.position),
          })),
          center: poly.center,
        })),
      };

      const response = await polygonService.updatePolygonConfig(payload);
      toast.success(`Configuration updated successfully! Message ID: ${response.message_id}`);

      // Optional: You can monitor the command status here if needed
      // Similar to the image capture functionality
      
    } catch (error) {
      console.error("Failed to save polygon config:", error);
      toast.error(
        error instanceof Error 
          ? error.message 
          : "Failed to update polygon configuration"
      );
    } finally {
      setIsSaving(false);
    }
  }, [deviceId]);

  return {
    isLoadingConfig,
    isSaving,
    loadPolygonConfig,
    savePolygonConfig,
  };
};