"use client";

import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import React from "react";
import { FilterCard } from "./FilterCard";

const ALL_TRAFFIC = [
  { id: "Large", label: "大型" },
  { id: "Car", label: "車" },
  { id: "Bike", label: "二輪車" },
  { id: "Bicycle", label: "自転車" },
];

interface TrafficFilterProps {
  selectedTrafficTypes: string[];
  onSelectionChange: (selectedTrafficTypes: string[]) => void;
  icon?: React.ReactNode;
  iconBgColor?: string;
  collapsible?: boolean;
  defaultExpanded?: boolean;
}

export function TrafficFilter({
  selectedTrafficTypes,
  onSelectionChange,
  icon,
  iconBgColor,
  collapsible = false,
  defaultExpanded = true,
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

  // 選択状況の文字列を生成
  const selectionSummary = `(${selectedTrafficTypes.length}/${ALL_TRAFFIC.length})`;

  return (
    <FilterCard
      title="交通種別"
      icon={icon}
      iconBgColor={iconBgColor}
      collapsible={collapsible}
      defaultExpanded={defaultExpanded}
      selectionSummary={selectionSummary} // 選択状況を渡す
    >
      <div className="space-y-3">
        {/* Select All Option */}
        <div className="flex items-center space-x-2 p-1 hover:bg-slate-50 rounded-lg transition-colors duration-200 group">
          <Checkbox
            id="select-all-traffic"
            checked={isAllSelected}
            onCheckedChange={handleSelectAllToggle}
            className="data-[state=checked]:bg-blue-500 data-[state=checked]:border-blue-500 cursor-pointer"
          />
          <Label
            htmlFor="select-all-traffic"
            className="text-sm font-medium text-slate-700 group-hover:text-slate-900 cursor-pointer"
          >
            すべて
          </Label>
        </div>

        {/* Individual Traffic Type Options */}
        <div>
          <div className="text-xs text-slate-500 font-medium mb-2">
            個別選択:
          </div>
          <div className="grid grid-cols-2 gap-2">
            {ALL_TRAFFIC.map((traffic) => (
              <div
                key={traffic.id}
                className="flex items-center space-x-2 p-1 hover:bg-slate-50 rounded-lg transition-colors duration-200 group"
              >
                <Checkbox
                  id={`traffic-${traffic.id}`}
                  checked={selectedTrafficTypes.includes(traffic.id)}
                  onCheckedChange={() => handleTrafficToggle(traffic.id)}
                  className="data-[state=checked]:bg-blue-500 data-[state=checked]:border-blue-500 cursor-pointer"
                />
                <Label
                  htmlFor={`traffic-${traffic.id}`}
                  className="text-sm text-slate-600 group-hover:text-slate-800 cursor-pointer transition-colors"
                >
                  {traffic.label}
                </Label>
              </div>
            ))}
          </div>
        </div>
      </div>
    </FilterCard>
  );
}
