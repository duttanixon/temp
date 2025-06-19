"use client";

import React, { useEffect, useState } from "react";
import { RefreshCw, Loader2, Save } from "lucide-react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Types and Utils
import { Device } from "@/types/device";
import { deviceService } from "@/services/deviceService";
import { LEAFLET_CONFIG } from "@/utils/analytics/city_eye/polygon.utils";

// Custom Hooks
import { usePolygonManager } from "@/hooks/analytics/city_eye/usePolygonManager";
import { useImageCapture } from "@/hooks/analytics/city_eye/useImageCapture";
import { usePolygonConfig } from "@/hooks/analytics/city_eye/usePolygonConfig";

// Components
import { Button } from "@/components/ui/button";
import { PolygonList } from "../../_components/PolygonList";
import { PolygonEditor } from "../../_components/PolygonEditor";
import { MapEditor } from "../../_components/MapEditor";
import { ToggleButton } from "../../_components/ToggleButton";

// Configure Leaflet icons
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions(LEAFLET_CONFIG);

interface PolygonEditorProps {
  device: Device;
}

// Main component - now much cleaner and focused on orchestration
export default function PolygonSettingsForm({ device }: PolygonEditorProps) {
  const [activeTab, setActiveTab] = useState<"zone" | "map">("zone");
  const [isOsm, setIsOsm] = useState(true);

  // Use custom hooks for state management
  const {
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
  } = usePolygonManager();

  const {
    isCapturing,
    imageUrl,
    isLoadingImage,
    loadDeviceImage,
    handleCaptureImage,
  } = useImageCapture(device.device_id);

  const {
    isLoadingConfig,
    isSaving,
    loadPolygonConfig,
    savePolygonConfig,
  } = usePolygonConfig(device.device_id, setPolygons, setPolygonsState);

  // Load initial data
  useEffect(() => {
    loadDeviceImage();
    loadPolygonConfig();

    return () => {
      if (imageUrl) {
        deviceService.revokeImageUrl(imageUrl);
      }
    };
  }, [device.device_id]);

  // Handle drag end for vertices
  const handleDragEnd = (event: any) => {
    const { active, delta } = event;
    updatePolygonVertices(active.id, delta.x, delta.y);
  };

  // Handle form submission
  const handleSubmit = async () => {
    await savePolygonConfig(polygons);
  };

  // Show loading state
  if (isLoadingConfig) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="container mx-auto">
      <div className="bg-white shadow-lg rounded-lg">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-800">
            {device.location} {device.name}
          </h2>
          <Button
            variant="outline"
            size="sm"
            onClick={handleCaptureImage}
            disabled={isCapturing}
          >
            {isCapturing ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="mr-2 h-4 w-4" />
            )}
            Update Image
          </Button>
        </div>

        {/* Content */}
        <div className="overflow-x-auto">
          <div className="flex gap-6 p-6" style={{ minWidth: "1320px" }}>
            {/* Left Panel - Polygon List */}
            <PolygonList
              polygons={polygons}
              polygonsState={polygonsState}
              onToggleVisibility={togglePolygonVisibility}
              onToggleActive={togglePolygonActiveState}
              onRemove={removePolygon}
              onAdd={addPolygon}
              onNameChange={updatePolygonName}
            />

            {/* Right Panel - Content Area */}
            <div className="flex-1">
              {/* Tab Navigation */}
              <div className="mb-4">
                <ToggleButton
                  checked={activeTab === "map"}
                  onChange={(checked) => setActiveTab(checked ? "map" : "zone")}
                  uncheckedLabel="ゾーン設定"
                  checkedLabel="マップ設定"
                />
              </div>

              {/* Tab Content */}
              {activeTab === "zone" ? (
                <PolygonEditor
                  polygons={polygons}
                  polygonsState={polygonsState}
                  imageUrl={imageUrl}
                  isLoadingImage={isLoadingImage}
                  onDragEnd={handleDragEnd}
                />
              ) : (
                <MapEditor
                  polygons={polygons}
                  polygonsState={polygonsState}
                  isOsm={isOsm}
                  onToggleMap={setIsOsm}
                  onUpdateRouteMarker={updateRouteMarker}
                />
              )}
            </div>
          </div>
        </div>

        {/* Submit Button */}
        <div className="p-6 bg-gray-50 border-t border-gray-200">
          <button
            onClick={handleSubmit}
            disabled={isSaving}
            className="w-full py-3 bg-blue-600 text-white font-semibold rounded-lg shadow-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-opacity-75 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
          >
            {isSaving ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                Saving Configuration...
              </>
            ) : (
              <>
                <Save className="mr-2 h-5 w-5" />
                Update Detection Zones
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
