import React from 'react';
import { DndContext } from '@dnd-kit/core';
import { Loader2 } from 'lucide-react';
import { EditablePolygon } from './EditablePolygon';
import { PolygonWithRoute, PolygonStates } from '@/types/cityeye/cityEyePolygon';

interface PolygonEditorProps {
  polygons: PolygonWithRoute[];
  polygonsState: PolygonStates;
  imageUrl: string;
  isLoadingImage: boolean;
  onDragEnd: (event: any) => void;
}

// Component for the zone editor view
export const PolygonEditor: React.FC<PolygonEditorProps> = ({
  polygons,
  polygonsState,
  imageUrl,
  isLoadingImage,
  onDragEnd,
}) => {
  return (
    <DndContext onDragEnd={onDragEnd}>
      <div className="relative h-[563px] w-[1000px] bg-black rounded-lg overflow-hidden">
        {isLoadingImage ? (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
            <Loader2 className="h-8 w-8 animate-spin text-white" />
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
  );
};
