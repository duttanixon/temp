import React from 'react';
import { Eye, EyeOff, Trash2, Plus } from 'lucide-react';
import { PolygonWithRoute, PolygonStates } from '@/types/cityeye/cityEyePolygon';
import { POLYGON_CONFIG } from '@/utils/analytics/city_eye/polygon.utils';

interface PolygonListProps {
  polygons: PolygonWithRoute[];
  polygonsState: PolygonStates;
  onToggleVisibility: (id: string) => void;
  onToggleActive: (id: string) => void;
  onRemove: (index: number) => void;
  onAdd: () => void;
  onNameChange: (index: number, name: string) => void;
}

// Component for polygon list sidebar
export const PolygonList: React.FC<PolygonListProps> = ({
  polygons,
  polygonsState,
  onToggleVisibility,
  onToggleActive,
  onRemove,
  onAdd,
  onNameChange,
}) => {
  return (
    <div className="w-[400px] flex-shrink-0 flex flex-col gap-2">
      {polygons.map((polygon, index) => (
        <div
          key={polygon.polygonId}
          className={`flex items-center justify-between rounded-lg px-4 py-2 cursor-pointer transition-colors ${
            polygonsState[polygon.polygonId]?.active
              ? "bg-purple-100"
              : "hover:bg-gray-50"
          }`}
          onClick={() => onToggleActive(polygon.polygonId)}
        >
          <div className="flex-1">
            <input
              type="text"
              value={polygon.name}
              onChange={(e) => {
                e.stopPropagation();
                onNameChange(index, e.target.value);
              }}
              onClick={(e) => e.stopPropagation()}
              className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-purple-500"
              maxLength={POLYGON_CONFIG.MAX_NAME_LENGTH}
            />
            <span className="text-xs text-gray-500 mt-1">
              Max {POLYGON_CONFIG.MAX_NAME_LENGTH} characters
            </span>
          </div>
          <div className="flex gap-2 ml-4">
            <button
              onClick={(e) => {
                e.stopPropagation();
                onToggleVisibility(polygon.polygonId);
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
                onRemove(index);
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
        onClick={onAdd}
        disabled={polygons.length >= POLYGON_CONFIG.MAX_POLYGONS}
        className={`mt-2 py-2 rounded-lg border transition-colors ${
          polygons.length >= POLYGON_CONFIG.MAX_POLYGONS
            ? "bg-gray-100 text-gray-400 cursor-not-allowed"
            : "bg-white text-purple-600 border-purple-600 hover:bg-purple-50"
        }`}
      >
        <Plus size={20} className="mx-auto" />
      </button>
    </div>
  );
};