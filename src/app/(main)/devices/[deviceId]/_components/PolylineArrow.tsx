import React, { useEffect } from 'react';
import { Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import { Point } from '@/types/cityeye/cityEyePolygon';

interface PolylineArrowProps {
  positions: Point[];
  color?: string;
}

// Component for rendering polyline with arrow on map
export const PolylineArrow: React.FC<PolylineArrowProps> = ({
  positions,
  color = "#7048ec",
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
      iconAnchor: [5, 5],
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