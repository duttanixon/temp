"use client";

import React from "react"; // Removed useState, useEffect
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { FilterCard } from "./FilterCard";

const ALL_TRAFFIC = [
  { id: "Large", label: "大型" }, // Assuming these IDs match backend expectations
  { id: "Car", label: "車" }, // "normal" in backend schema, might need mapping if these are directly used
  { id: "Bike", label: "二輪車" }, // "motorcycle" in backend
  { id: "Bicycle", label: "自転車" },
];

interface TrafficFilterProps {
  selectedTrafficTypes: string[]; // Changed prop name to be more specific
  onSelectionChange: (selectedTrafficTypes: string[]) => void;
}

export function TrafficFilter({
  selectedTrafficTypes,
  onSelectionChange,
}: TrafficFilterProps) {
  const isAllSelected =
    ALL_TRAFFIC.length > 0 &&
    selectedTrafficTypes.length === ALL_TRAFFIC.length;

  const handleTrafficToggle = (trafficId: string) => {
    const newSelectedTrafficTypes = selectedTrafficTypes.includes(trafficId)
      ? selectedTrafficTypes.filter((t) => t !== trafficId)
      : [...selectedTrafficTypes, trafficId];
    onSelectionChange(newSelectedTrafficTypes);
  };

  const handleSelectAllToggle = () => {
    if (isAllSelected) {
      onSelectionChange([]);
    } else {
      onSelectionChange(ALL_TRAFFIC.map((t) => t.id));
    }
  };

  return (
    <FilterCard title="交通種別">
      {" "}
      {/* Changed title to be more specific */}
      <div className="space-y-2">
        <div className="flex items-center space-x-2">
          <Checkbox
            id="select-all-traffic"
            checked={isAllSelected}
            onCheckedChange={handleSelectAllToggle}
            className="cursor-pointer"
          />
          <Label htmlFor="select-all-traffic" className="text-sm font-medium">
            {" "}
            {/* Corrected htmlFor */}
            すべて
          </Label>
        </div>
        {ALL_TRAFFIC.map((traffic) => (
          <div key={traffic.id} className="flex items-center space-x-2">
            <Checkbox
              id={`traffic-${traffic.id}`}
              checked={selectedTrafficTypes.includes(traffic.id)}
              onCheckedChange={() => handleTrafficToggle(traffic.id)}
              className="cursor-pointer"
            />
            <Label
              htmlFor={`traffic-${traffic.id}`}
              className="text-sm font-normal"
            >
              {traffic.label}
            </Label>
          </div>
        ))}
      </div>
    </FilterCard>
  );
}
