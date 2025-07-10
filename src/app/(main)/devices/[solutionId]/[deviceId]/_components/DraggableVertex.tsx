import React from 'react';
import { useDraggable } from '@dnd-kit/core';

interface DraggableVertexProps {
  id: string;
  x: number;
  y: number;
  color: string;
  isActive: boolean;
}

// Reusable draggable vertex component
export const DraggableVertex: React.FC<DraggableVertexProps> = ({
  id,
  x,
  y,
  color,
  isActive,
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