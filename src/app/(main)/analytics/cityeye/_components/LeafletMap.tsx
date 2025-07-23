"use client";
import L from "leaflet";
import "leaflet-arrowheads";
import "leaflet/dist/leaflet.css";
import { useEffect, useRef } from "react";
import {
  MapContainer,
  Marker,
  Polyline,
  TileLayer,
  Tooltip,
  useMap,
} from "react-leaflet";

// 依存型などもこのファイルで宣言/インポート
type ArrowPolylineProps = {
  positions: [number, number][];
  color: string;
  weight?: number;
  tooltip?: React.ReactNode;
};

type PolylineProps = {
  points: [number, number][];
  start: { lat: number; lng: number };
  end: { lat: number; lng: number };
  type: string;
  count: number;
  name: string;
};

const AutoZoom = ({
  coordinates,
  hasAttemptedFetch,
}: {
  coordinates: [number, number][];
  hasAttemptedFetch: boolean;
}) => {
  const map = useMap();
  useEffect(() => {
    if (!(hasAttemptedFetch && coordinates.length > 0)) return;
    const timer = setTimeout(() => {
      if (hasAttemptedFetch && coordinates.length > 0) {
        map.fitBounds(coordinates, { padding: [30, 30] });
      }
    }, 0);
    return () => clearTimeout(timer);
  }, [coordinates, hasAttemptedFetch, map]);
  return null;
};

const ArrowPolyline = ({
  positions,
  color,
  weight = 4,
  tooltip,
}: ArrowPolylineProps) => {
  const polylineRef = useRef<L.Polyline>(null);
  useEffect(() => {
    if (polylineRef.current) {
      polylineRef.current.arrowheads({
        size: "12px",
        frequency: "endonly",
        yawn: 60,
        color,
        fill: true,
      });
    }
  }, [positions, color]);
  return (
    <Polyline
      positions={positions}
      pathOptions={{ color, weight, lineCap: "butt", lineJoin: "miter" }}
      ref={polylineRef}
    >
      {tooltip && (
        <Tooltip direction="auto" offset={[5, -5]}>
          {tooltip}
        </Tooltip>
      )}
    </Polyline>
  );
};

type LeafletMapProps = {
  polylines: PolylineProps[];
  coordinatesForZoom: [number, number][];
  hasAttemptedFetch: boolean;
  zoneLabels: {
    name: string;
    lat: number;
    lng: number;
  }[];
  resetKey: number;
  legendItems: {
    color: string;
    label: string;
  }[];
  thresholds: number[];
  allDetectionZones?: {
    name: string;
    deviceLocation?: string;
    deviceName?: string;
  }[];
};

export default function LeafletMap({
  polylines,
  coordinatesForZoom,
  hasAttemptedFetch,
  zoneLabels,
  resetKey,
  legendItems,
  thresholds,
  allDetectionZones = [],
}: LeafletMapProps) {
  return (
    <MapContainer
      key={resetKey}
      zoom={19}
      style={{
        height: "100%",
        width: "100%",
        borderRadius: "0.5rem",
      }}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <AutoZoom
        coordinates={coordinatesForZoom}
        hasAttemptedFetch={hasAttemptedFetch}
      />
      {/* 矢印線描画 */}
      {polylines.map((line, index) => {
        let color = "#4A83BD"; // デフォルトの青色
        let legendLabel = legendItems[0].label;
        if (line.count >= thresholds[2]) {
          color = legendItems[3].color;
          legendLabel = legendItems[3].label;
        } else if (line.count >= thresholds[1]) {
          color = legendItems[2].color;
          legendLabel = legendItems[2].label;
        } else if (line.count >= thresholds[0]) {
          color = legendItems[1].color;
          legendLabel = legendItems[1].label;
        }
        return (
          <ArrowPolyline
            key={index}
            positions={[
              [line.start.lat, line.start.lng],
              [line.end.lat, line.end.lng],
            ]}
            color={color}
            weight={10}
            tooltip={
              <>
                <div style={{ fontWeight: "bold" }}>
                  {(() => {
                    const zoneObj = allDetectionZones.find(
                      (z) => z.name === line.name
                    );
                    return zoneObj?.deviceLocation && zoneObj?.deviceName
                      ? `${zoneObj.deviceLocation}_${zoneObj.deviceName}`
                      : `${zoneObj?.deviceLocation ?? zoneObj?.deviceName ?? "不明なデバイス"}`;
                  })()}
                </div>
                <div>領域名: {line.name}</div>
                <div>方向: {line.type}</div>
                <div style={{ height: 8 }} />
                <div>
                  {legendLabel} ({line.count.toLocaleString()} 人)
                </div>
              </>
            }
          />
        );
      })}
      {/* zoneごとにラベルを1つだけ表示 */}
      {zoneLabels.map((label, idx) => {
        const textLength = label.name.length;
        const iconWidth = Math.max(24, textLength * 24); // 1文字あたり24pxの幅を計算
        const iconHeight = 30; // 高さは固定
        const iconAnchorX = iconWidth / 2; // 横方向の中心
        const iconAnchorY = iconHeight / 2; // 縦方向の中心
        return (
          <Marker
            key={label.name + idx}
            position={[label.lat, label.lng]}
            interactive={false}
            icon={L.divIcon({
              className: "zone-label-marker",
              html: `<div style="font-size:24px;font-weight:semi-bold;color:#333;white-space:nowrap;display:flex;align-items:center;justify-content:center;">${label.name}</div>`,
              iconSize: [iconWidth, iconHeight], // zoneごとに計算されたサイズ
              iconAnchor: [iconAnchorX, iconAnchorY], // zoneごとに計算されたアンカー
            })}
          />
        );
      })}
    </MapContainer>
  );
}
