import React, { useRef, useMemo } from 'react';
import { Marker } from 'react-leaflet';
import { Point } from '@/types/cityeye/cityEyePolygon';

interface DraggableMapMarkerProps {
  position: Point;
  onDrag: (position: Point) => void;
  label: string;
}

// Component for draggable markers on the map
export const DraggableMapMarker: React.FC<DraggableMapMarkerProps> = ({
  position,
  onDrag,
  label,
}) => {
  const markerRef = useRef<any>(null);

  const eventHandlers = useMemo(
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
    />
  );
};