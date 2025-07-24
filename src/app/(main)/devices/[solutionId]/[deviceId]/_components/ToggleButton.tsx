import React from 'react';

interface ToggleButtonProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  uncheckedLabel: string;
  checkedLabel: string;
}

// Reusable toggle button component
export const ToggleButton: React.FC<ToggleButtonProps> = ({
  checked,
  onChange,
  uncheckedLabel,
  checkedLabel,
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