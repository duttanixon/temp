import React, { useMemo } from 'react';
import { DraggableVertex } from './DraggableVertex';
import { PolygonWithRoute } from '@/types/cityeye/cityEyePolygon';
import { POLYGON_CONFIG } from '@/utils/analytics/city_eye/polygon.utils';

interface EditablePolygonProps {
  polygon: PolygonWithRoute;
  isActive: boolean;
  isVisible: boolean;
}

// Component for rendering editable polygons
export const EditablePolygon: React.FC<EditablePolygonProps> = ({
  polygon,
  isActive,
  isVisible,
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
          fill={POLYGON_CONFIG.COLORS.PRIMARY_ALPHA}
          stroke={POLYGON_CONFIG.COLORS.PRIMARY}
          strokeWidth="2"
        />
      </svg>
      {polygon.vertices.map((vertex) => (
        <DraggableVertex
          key={vertex.vertexId}
          id={vertex.vertexId}
          x={vertex.position.x}
          y={vertex.position.y}
          color={POLYGON_CONFIG.COLORS.PRIMARY}
          isActive={isActive}
        />
      ))}
    </>
  );
};