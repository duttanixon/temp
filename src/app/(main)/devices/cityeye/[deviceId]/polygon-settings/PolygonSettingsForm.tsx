"use client";

import React, { useState, useMemo, useEffect } from "react";
import { DndContext, useDraggable } from "@dnd-kit/core";
import {
  MapContainer,
  TileLayer,
  Marker,
  Polyline,
  useMap,
} from "react-leaflet";
import { Eye, EyeOff, Trash2, Plus, RefreshCw, Loader2 } from "lucide-react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { Device } from "@/types/device";
import { deviceService } from "@/services/deviceService";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";

delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "/images/media/marker-icon-2x.png",
  iconUrl: "/images/media/marker-icon.png",
  shadowUrl: "/images/media/marker-shadow.png",
});

// --- TYPE DEFINITIONS ---
type Vertex = {
  vertexId: string;
  position: { x: number; y: number };
};

type LatLngLiteral = {
  lat: number;
  lng: number;
};

type Route = {
  center: {
    startPoint: LatLngLiteral;
    endPoint: LatLngLiteral;
  };
};

type Polygon = {
  polygonId: string;
  name: string;
  vertices: Vertex[];
};

type PolygonWithRoute = Polygon & Route;

type PolygonState = {
  visible: boolean;
  active: boolean;
};

// --- UTILITY FUNCTIONS ---
const convertPosition = ({
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

// Draggable Vertex Component
const DraggableVertex = ({
  id,
  x,
  y,
  color,
  isActive,
}: {
  id: string;
  x: number;
  y: number;
  color: string;
  isActive: boolean;
}) => {
  const { attributes, listeners, setNodeRef, transform } = useDraggable({ id });

  const style = {
    position: "absolute" as const,
    left: x,
    top: y,
    transform: transform
      ? `translate3d(${transform.x}px, ${transform.y}px, 0)`
      : "translate(-50%, -50%)",
    touchAction: "none",
    display: isActive ? "block" : "none",
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
      className="z-20 w-[10px] h-[10px] bg-white border-2 shadow-lg cursor-grab active:cursor-grabbing box-border"
    >
      <div className="w-full h-full" style={{ borderColor: color }}></div>
    </div>
  );
};

// Editable Polygon Component
const EditablePolygon = ({
  polygon,
  isActive,
  isVisible,
}: {
  polygon: PolygonWithRoute;
  isActive: boolean;
  isVisible: boolean;
}) => {
  const points = useMemo(
    () =>
      polygon.vertices.map((v) => `${v.position.x},${v.position.y}`).join(" "),
    [polygon.vertices]
  );

  if (!isVisible) return null;

  return (
    <>
      <svg
        className="absolute top-0 left-0 w-full h-full pointer-events-none"
        style={{ zIndex: 10 }}
      >
        <polygon
          points={points}
          fill="#7048ec7f"
          stroke="#7048ec"
          strokeWidth="2"
        />
      </svg>
      {polygon.vertices.map((vertex) => (
        <DraggableVertex
          key={vertex.vertexId}
          id={vertex.vertexId}
          x={vertex.position.x}
          y={vertex.position.y}
          color="#7048ec"
          isActive={isActive}
        />
      ))}
    </>
  );
};

// Polyline with Arrow Component for Map - FIXED VERSION
const PolylineArrow = ({
  positions,
  color = "#7048ec",
}: {
  positions: LatLngLiteral[];
  color?: string;
}) => {
  const map = useMap();

  useEffect(() => {
    if (positions.length < 2) return;

    const start = positions[0];
    const end = positions[1];
    const deltaX = end.lng - start.lng; // Longitude difference (East is positive)
    const deltaY = -(end.lat - start.lat); // Latitude difference (NEGATED for screen coords)
    const angleInRadians = Math.atan2(deltaY, deltaX);
    const angleInDegrees = (angleInRadians * 180) / Math.PI;
    const adjustedAngle = angleInDegrees - 45;

    const arrowHead = L.divIcon({
      className: "arrow-head",
      html: `<div style="
        width: 0;
        height: 0;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-bottom: 10px solid ${color};
        transform: rotate(${adjustedAngle}deg);
        transform-origin: center center;
      "></div>`,
      iconSize: [10, 10],
      iconAnchor: [5, 5], // Center the arrow on the point
    });

    const marker = L.marker([end.lat, end.lng], {
      icon: arrowHead,
    }).addTo(map);

    return () => {
      map.removeLayer(marker);
    };
  }, [map, positions, color]);

  return <Polyline positions={positions} color={color} />;
};

// Draggable Map Marker Component
const DraggableMapMarker = ({
  position,
  onDrag,
  label,
}: {
  position: LatLngLiteral;
  onDrag: (position: LatLngLiteral) => void;
  label: string;
}) => {
  const markerRef = React.useRef<any>(null);

  const eventHandlers = React.useMemo(
    () => ({
      dragend() {
        const marker = markerRef.current;
        if (marker != null) {
          onDrag(marker.getLatLng());
        }
      },
    }),
    [onDrag]
  );

  return (
    <Marker
      draggable={true}
      eventHandlers={eventHandlers}
      position={position}
      ref={markerRef}
    ></Marker>
  );
};

// Toggle Button Component
const ToggleButton = ({
  checked,
  onChange,
  uncheckedLabel,
  checkedLabel,
}: {
  checked: boolean;
  onChange: (checked: boolean) => void;
  uncheckedLabel: string;
  checkedLabel: string;
}) => {
  return (
    <div className="grid h-10 grid-cols-2 items-center justify-center rounded-md bg-purple-100 p-1 text-sm text-gray-600">
      <div
        className={`flex h-full w-full cursor-pointer items-center justify-center rounded ${!checked ? "bg-white text-purple-600" : ""}`}
        onClick={() => onChange(false)}
      >
        <span>{uncheckedLabel}</span>
      </div>
      <div
        className={`flex h-full w-full cursor-pointer items-center justify-center rounded ${checked ? "bg-white text-purple-600" : ""}`}
        onClick={() => onChange(true)}
      >
        <span>{checkedLabel}</span>
      </div>
    </div>
  );
};

// Main Polygon Editor Component
export default function PolygonEditor({ device }: { device: Device }) {
  const [polygons, setPolygons] = useState<PolygonWithRoute[]>([]);
  const [polygonsState, setPolygonsState] = useState<
    Record<string, PolygonState>
  >({});

  const [activeTab, setActiveTab] = useState<"zone" | "map">("zone");
  const [isOsm, setIsOsm] = useState(true);

  // --- Image caputre state---
  const [isCapturing, setIsCapturing] = useState(false);
  const [imageUrl, setImageUrl] = useState<string>("");
  const [isLoadingImage, setIsLoadingImage] = useState(true);

  // Function to load image
  const loadDeviceImage = async () => {
    try {
      setIsLoadingImage(true);
      const url = await deviceService.getDeviceImage(
        device.device_id,
        "cityeye"
      );
      setImageUrl(url);
    } catch (error) {
      console.error("Failed to load device image:", error);
      toast.error("Failed to load device image");
    } finally {
      setIsLoadingImage(false);
    }
  };

  // Load initial image
  useEffect(() => {
    loadDeviceImage();

    // Cleanup function to revoke the blob URL when component unmounts
    return () => {
      if (imageUrl) {
        deviceService.revokeImageUrl(imageUrl);
      }
    };
  }, [device.device_id]);

  // Toggle polygon visibility
  const togglePolygonVisibility = (id: string) => {
    setPolygonsState((prev) => ({
      ...prev,
      [id]: {
        ...prev[id],
        visible: !prev[id].visible,
      },
    }));
  };

  // Toggle polygon active state
  const togglePolygonActiveState = (selectedId: string) => {
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
  };

  // Add new polygon
  const addPolygon = () => {
    if (polygons.length >= 8) return; // Max 8 polygons

    const existingIds = polygons
      .map((p) => parseInt(p.polygonId, 10))
      .sort((a, b) => a - b);
    const newId = existingIds.reduce(
      (acc, cur) => (acc === cur ? acc + 1 : acc),
      1
    );
    const newPolygonId = newId.toString();

    const newPolygon: PolygonWithRoute = {
      polygonId: newPolygonId,
      name: `New Zone ${newPolygonId}`,
      vertices: [
        { vertexId: `${newPolygonId}-1`, position: { x: 10, y: 10 } },
        { vertexId: `${newPolygonId}-2`, position: { x: 200, y: 10 } },
        { vertexId: `${newPolygonId}-3`, position: { x: 200, y: 200 } },
        { vertexId: `${newPolygonId}-4`, position: { x: 10, y: 200 } },
      ],
      center: {
        startPoint: { lat: 36.5287, lng: 139.8147 },
        endPoint: { lat: 36.5285, lng: 139.8144 },
      },
    };

    setPolygons((prev) => [...prev, newPolygon]);
    setPolygonsState((prev) => ({
      ...prev,
      [newPolygonId]: { visible: true, active: true },
    }));
  };

  // Remove polygon
  const removePolygon = (index: number) => {
    const polygonId = polygons[index].polygonId;
    setPolygons((prev) => prev.filter((_, i) => i !== index));
    setPolygonsState((prev) => {
      const newState = { ...prev };
      delete newState[polygonId];
      return newState;
    });
  };

  // Update polygon name
  const updatePolygonName = (index: number, name: string) => {
    setPolygons((prev) =>
      prev.map((poly, i) => (i === index ? { ...poly, name } : poly))
    );
  };

  // Handle drag end for vertices
  const handleDragEnd = (event: any) => {
    const { active, delta } = event;

    setPolygons((prevPolygons) =>
      prevPolygons.map((poly) => ({
        ...poly,
        vertices: poly.vertices.map((vertex) =>
          vertex.vertexId === active.id
            ? {
                ...vertex,
                position: {
                  x: Math.round(vertex.position.x + delta.x),
                  y: Math.round(vertex.position.y + delta.y),
                },
              }
            : vertex
        ),
      }))
    );
  };

  // Update route markers
  const updateRouteMarker = (
    polygonId: string,
    point: "start" | "end",
    position: LatLngLiteral
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
  };

  // Submit handler
  const handleSubmit = () => {
    const dataToSend = {
      detectionZones: polygons.map((poly) => ({
        ...poly,
        vertices: poly.vertices.map((v) => ({
          ...v,
          position: convertPosition({
            position: v.position,
            inputWidth: 1000,
            inputHeight: 563,
            targetWidth: 1280,
            targetHeight: 720,
          }),
        })),
      })),
    };

    console.log("Submitting data:", JSON.stringify(dataToSend, null, 2));
    alert("Check console for JSON data that would be sent to API");
  };

  const handleCaptureImage = async () => {
    setIsCapturing(true);
    toast.info("Requesting new image from device...");
    let eventSource: EventSource | null = null;
  
    try {
      const { message_id } = await deviceService.captureImage(device.device_id);
  
      // Create EventSource with the proxied endpoint
      eventSource = new EventSource(
        `/api/sse/commands/status/${message_id}`
      );
  
      // Handle incoming messages
      eventSource.onmessage = async (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log("SSE message received:", data);
  
          if (data.status === "SUCCESS") {
            toast.success("Image captured successfully! Refreshing...");
            
            // Revoke old image URL to prevent memory leak
            if (imageUrl) {
              deviceService.revokeImageUrl(imageUrl);
            }
            
            // Load the new image
            await loadDeviceImage();
            
            eventSource?.close();
            setIsCapturing(false);
          } else if (data.status === "FAILED" || data.status === "TIMEOUT") {
            const errorMsg = data.error_message || data.error || "Unknown error";
            toast.error(`Failed to capture image: ${errorMsg}`);
            eventSource?.close();
            setIsCapturing(false);
          } else if (data.heartbeat) {
            console.log("SSE heartbeat received");
          } else {
            // Status update (PENDING, SENT, etc.)
            console.log(`Command status: ${data.status}`);
          }
        } catch (parseError) {
          console.error("Error parsing SSE data:", parseError, event.data);
        }
      };
  
      // Handle connection errors
      eventSource.onerror = (error) => {
        console.error("SSE connection error:", error);
        
        // Check if the connection was closed normally
        if (eventSource?.readyState === EventSource.CLOSED) {
          console.log("SSE connection closed");
        } else {
          toast.error("Connection to status updates failed. Please try again.");
        }
        
        eventSource?.close();
        setIsCapturing(false);
      };
  
      // Handle connection open
      eventSource.onopen = () => {
        console.log("SSE connection established");
      };
  
      // Set a timeout in case the command takes too long
      const timeout = setTimeout(() => {
        if (eventSource?.readyState !== EventSource.CLOSED) {
          toast.error("Command timed out. Please try again.");
          eventSource?.close();
          setIsCapturing(false);
        }
      }, 1 * 60 * 1000); // 5 minutes timeout
  
      // Clean up timeout when event source closes
      eventSource.addEventListener('close', () => {
        clearTimeout(timeout);
      });
  
    } catch (error) {
      console.error("Failed to initiate capture command:", error);
      toast.error("Failed to send capture command to the device.");
      eventSource?.close();
      setIsCapturing(false);
    }
  };
  

  const mapCenter: LatLngLiteral = { lat: 36.5287, lng: 139.8147 };

  return (
    <div className="w-full p-4">
      <div className="bg-white rounded-xl shadow-2xl overflow-hidden">
        <div className="flex items-center justify-between p-6 border-b border-gray-200 justify-between">
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

        {/* This new container makes the content horizontally scrollable on small screens */}
        <div className="overflow-x-auto">
          <div className="flex gap-6 p-6" style={{ minWidth: "1320px" }}>
            {/* Left Panel - Polygon List */}
            <div className="w-[400px] flex-shrink-0 flex flex-col gap-2">
              {polygons.map((polygon, index) => (
                <div
                  key={polygon.polygonId}
                  className={`flex items-center justify-between rounded-lg px-4 py-2 cursor-pointer transition-colors ${
                    polygonsState[polygon.polygonId]?.active
                      ? "bg-purple-100"
                      : "hover:bg-gray-50"
                  }`}
                  onClick={() => togglePolygonActiveState(polygon.polygonId)}
                >
                  <div className="flex-1">
                    <input
                      type="text"
                      value={polygon.name}
                      onChange={(e) => {
                        e.stopPropagation();
                        updatePolygonName(index, e.target.value);
                      }}
                      onClick={(e) => e.stopPropagation()}
                      className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-purple-500"
                      maxLength={10}
                    />
                    <span className="text-xs text-gray-500 mt-1">
                      Max 10 characters
                    </span>
                  </div>
                  <div className="flex gap-2 ml-4">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        togglePolygonVisibility(polygon.polygonId);
                      }}
                      className="p-1 hover:bg-gray-200 rounded transition-colors"
                      aria-label={
                        polygonsState[polygon.polygonId]?.visible
                          ? "Hide zone"
                          : "Show zone"
                      }
                    >
                      {polygonsState[polygon.polygonId]?.visible ? (
                        <Eye size={20} className="text-gray-600" />
                      ) : (
                        <EyeOff size={20} className="text-gray-400" />
                      )}
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        removePolygon(index);
                      }}
                      className="p-1 hover:bg-gray-200 rounded transition-colors text-gray-500 hover:text-red-500"
                      aria-label="Delete zone"
                    >
                      <Trash2 size={20} />
                    </button>
                  </div>
                </div>
              ))}

              <button
                onClick={addPolygon}
                disabled={polygons.length >= 8}
                className={`mt-2 py-2 rounded-lg border transition-colors ${
                  polygons.length >= 8
                    ? "border-gray-300 text-gray-400 cursor-not-allowed"
                    : "border-purple-600 text-purple-600 hover:bg-purple-50 cursor-pointer"
                }`}
                aria-label="Add new zone"
              >
                <div className="flex items-center justify-center gap-2">
                  <Plus size={20} />
                  <span>Add Zone</span>
                </div>
              </button>
            </div>

            {/* Right Panel - Tabs */}
            <div className="">
              {/* Tab Navigation */}
              <div className="flex gap-2 mb-4">
                <button
                  onClick={() => setActiveTab("zone")}
                  className={`px-4 py-2 rounded-md transition-colors ${
                    activeTab === "zone"
                      ? "bg-blue-600 text-white"
                      : "bg-blue-100 text-blue-600 hover:bg-blue-200"
                  }`}
                >
                  Zone Setting
                </button>
                <button
                  onClick={() => setActiveTab("map")}
                  className={`px-4 py-2 rounded-md transition-colors ${
                    activeTab === "map"
                      ? "bg-blue-600 text-white"
                      : "bg-blue-100 text-blue-600 hover:bg-blue-200"
                  }`}
                >
                  Direction Setting
                </button>
              </div>

              {/* Tab Content */}
              {activeTab === "zone" ? (
                <DndContext onDragEnd={handleDragEnd}>
                  <div className="relative h-[563px] w-[1000px] bg-black rounded-lg overflow-hidden">
                    {isLoadingImage ? (
                      <div className="absolute inset-0 flex items-center justify-center">
                        <div className="text-white">Loading image...</div>
                      </div>
                    ) : imageUrl ? (
                      <img
                        src={imageUrl}
                        alt="Camera view"
                        className="absolute inset-0 w-full h-full object-cover opacity-80"
                      />
                    ) : (
                      <div className="absolute inset-0 flex items-center justify-center">
                        <div className="text-white">No image available</div>
                      </div>
                    )}
                    {polygons.map((polygon) => (
                      <EditablePolygon
                        key={polygon.polygonId}
                        polygon={polygon}
                        isActive={polygonsState[polygon.polygonId]?.active}
                        isVisible={polygonsState[polygon.polygonId]?.visible}
                      />
                    ))}
                  </div>
                </DndContext>
              ) : (
                <div className="relative">
                  <div className="absolute right-4 top-4 z-[1000] bg-white rounded-lg shadow-lg">
                    <ToggleButton
                      checked={isOsm}
                      onChange={setIsOsm}
                      uncheckedLabel="国土地理院"
                      checkedLabel="OpenStreetMap"
                    />
                  </div>
                  <MapContainer
                    center={mapCenter}
                    zoom={18}
                    className="h-[563px] w-[1000px] rounded-lg"
                  >
                    <TileLayer
                      attribution={
                        isOsm
                          ? '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                          : '&copy; <a href="https://maps.gsi.go.jp/development/ichiran.html">国土地理院</a>'
                      }
                      url={
                        isOsm
                          ? "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                          : "https://cyberjapandata.gsi.go.jp/xyz/std/{z}/{x}/{y}.png"
                      }
                    />
                    {polygons.map((polygon) =>
                      polygonsState[polygon.polygonId]?.visible ? (
                        <React.Fragment key={polygon.polygonId}>
                          {polygonsState[polygon.polygonId]?.active && (
                            <>
                              <DraggableMapMarker
                                position={polygon.center.startPoint}
                                onDrag={(pos) =>
                                  updateRouteMarker(
                                    polygon.polygonId,
                                    "start",
                                    pos
                                  )
                                }
                                label="Start"
                              />
                              <DraggableMapMarker
                                position={polygon.center.endPoint}
                                onDrag={(pos) =>
                                  updateRouteMarker(
                                    polygon.polygonId,
                                    "end",
                                    pos
                                  )
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
              )}
            </div>
          </div>
        </div>

        {/* Submit Button */}
        <div className="p-6 bg-gray-50 border-t border-gray-200">
          <button
            onClick={handleSubmit}
            className="w-full py-3 bg-blue-600 text-white font-semibold rounded-lg shadow-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-opacity-75 transition-colors"
          >
            Update Detection Zones
          </button>
        </div>
      </div>
    </div>
  );
}
