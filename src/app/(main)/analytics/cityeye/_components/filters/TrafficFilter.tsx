"use client";

import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Bike, Car, Mountain, Truck } from "lucide-react";
import React from "react";
import { FilterCard } from "./FilterCard";

const ALL_TRAFFIC = [
  {
    id: "Large",
    label: "大型",
    icon: <Truck className="w-4 h-4" />,
    color: "bg-red-100 text-red-700 border-red-200",
    hoverColor: "hover:bg-red-200",
  },
  {
    id: "Car",
    label: "車",
    icon: <Car className="w-4 h-4" />,
    color: "bg-blue-100 text-blue-700 border-blue-200",
    hoverColor: "hover:bg-blue-200",
  },
  {
    id: "Bike",
    label: "二輪車",
    icon: <Bike className="w-4 h-4" />,
    color: "bg-green-100 text-green-700 border-green-200",
    hoverColor: "hover:bg-green-200",
  },
  {
    id: "Bicycle",
    label: "自転車",
    icon: <Mountain className="w-4 h-4" />,
    color: "bg-yellow-100 text-yellow-700 border-yellow-200",
    hoverColor: "hover:bg-yellow-200",
  },
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

  // Quick select presets
  const quickSelectPresets = [
    { label: "車両", types: ["Large", "Car"] },
    { label: "二輪", types: ["Bike", "Bicycle"] },
    { label: "大型のみ", types: ["Large"] },
  ];

  const handleQuickSelect = (types: string[]) => {
    onSelectionChange(types);
  };

  return (
    <FilterCard
      title="交通種別"
      icon={icon}
      iconBgColor={iconBgColor}
      collapsible={collapsible}
      defaultExpanded={defaultExpanded}>
      <div className="space-y-4">
        {/* Select All Option */}
        <div className="flex items-center space-x-2 p-3 hover:bg-slate-50 rounded-lg transition-colors duration-200 group border border-slate-200">
          <Checkbox
            id="select-all-traffic"
            checked={isAllSelected}
            onCheckedChange={handleSelectAllToggle}
            className="data-[state=checked]:bg-green-500 data-[state=checked]:border-green-500"
          />
          <div className="flex items-center gap-2">
            <Car className="w-4 h-4 text-slate-500 group-hover:text-slate-700" />
            <Label
              htmlFor="select-all-traffic"
              className="text-sm font-medium text-slate-700 group-hover:text-slate-900 cursor-pointer">
              すべて ({selectedTrafficTypes.length}/{ALL_TRAFFIC.length})
            </Label>
          </div>
        </div>

        {/* Quick Select Presets */}
        <div className="space-y-2">
          <div className="text-xs text-slate-500 font-medium">
            クイック選択:
          </div>
          <div className="flex flex-wrap gap-2">
            {quickSelectPresets.map((preset) => (
              <button
                key={preset.label}
                onClick={() => handleQuickSelect(preset.types)}
                className="text-xs px-3 py-1.5 bg-green-50 hover:bg-green-100 text-green-700 rounded-full transition-colors duration-200 border border-green-200 hover:border-green-300">
                {preset.label}
              </button>
            ))}
          </div>
        </div>

        {/* Individual Traffic Type Options */}
        <div className="space-y-2">
          <div className="text-xs text-slate-500 font-medium">個別選択:</div>
          <div className="grid grid-cols-1 gap-2">
            {ALL_TRAFFIC.map((traffic) => {
              const isSelected = selectedTrafficTypes.includes(traffic.id);
              return (
                <div
                  key={traffic.id}
                  className={`flex items-center space-x-3 p-3 rounded-lg border transition-all duration-200 group cursor-pointer ${
                    isSelected
                      ? `${traffic.color} ${traffic.hoverColor}`
                      : "bg-slate-50 hover:bg-slate-100 border-slate-200 hover:border-slate-300"
                  }`}
                  onClick={() => handleTrafficToggle(traffic.id)}>
                  <Checkbox
                    id={`traffic-${traffic.id}`}
                    checked={isSelected}
                    onCheckedChange={() => handleTrafficToggle(traffic.id)}
                    className="data-[state=checked]:bg-green-500 data-[state=checked]:border-green-500"
                  />
                  <div className="flex items-center gap-3 flex-1">
                    <div
                      className={`p-2 rounded-lg transition-colors ${
                        isSelected
                          ? "bg-white/50"
                          : "bg-slate-200 group-hover:bg-slate-300"
                      }`}>
                      {traffic.icon}
                    </div>
                    <Label
                      htmlFor={`traffic-${traffic.id}`}
                      className={`text-sm font-medium cursor-pointer transition-colors ${
                        isSelected
                          ? "text-current"
                          : "text-slate-600 group-hover:text-slate-800"
                      }`}>
                      {traffic.label}
                    </Label>
                  </div>
                  <div className="ml-auto">
                    {isSelected && (
                      <div className="w-3 h-3 rounded-full bg-current opacity-60"></div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Selection Summary */}
        {selectedTrafficTypes.length > 0 && (
          <div className="mt-3 p-2 bg-green-50 border border-green-200 rounded-lg">
            <div className="text-xs text-green-700">
              選択済み:{" "}
              {selectedTrafficTypes
                .map((id) => ALL_TRAFFIC.find((t) => t.id === id)?.label)
                .join(", ")}
            </div>
          </div>
        )}
      </div>
    </FilterCard>
  );
}
