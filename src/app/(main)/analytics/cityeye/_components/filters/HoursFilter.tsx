"use client";

import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import React from "react";
import { FilterCard } from "./FilterCard";

const ALL_HOURS = Array.from({ length: 24 }, (_, i) => ({
  id: `${String(i).padStart(2, "0")}:00`,
  label: `${String(i).padStart(2, "0")}:00`,
}));

// Time period presets
const TIME_PRESETS = [
  {
    id: "morning",
    label: "朝 (6-12)",
    hours: ["06:00", "07:00", "08:00", "09:00", "10:00", "11:00"],
  },
  {
    id: "afternoon",
    label: "昼 (12-18)",
    hours: ["12:00", "13:00", "14:00", "15:00", "16:00", "17:00"],
  },
  {
    id: "evening",
    label: "夜 (18-24)",
    hours: ["18:00", "19:00", "20:00", "21:00", "22:00", "23:00"],
  },
  {
    id: "midnight",
    label: "深夜 (0-6)",
    hours: ["00:00", "01:00", "02:00", "03:00", "04:00", "05:00"],
  },
];

interface HoursFilterProps {
  selectedHours: string[];
  onSelectionChange: (selectedHours: string[]) => void;
  icon?: React.ReactNode;
  iconBgColor?: string;
  collapsible?: boolean;
  defaultExpanded?: boolean;
}

export function HoursFilter({
  selectedHours,
  onSelectionChange,
  icon,
  iconBgColor,
  collapsible = false,
  defaultExpanded = true,
}: HoursFilterProps) {
  const isAllSelected =
    ALL_HOURS.length > 0 && selectedHours.length === ALL_HOURS.length;

  const handleHourToggle = (hourId: string) => {
    const newSelectedHours = selectedHours.includes(hourId)
      ? selectedHours.filter((h) => h !== hourId)
      : [...selectedHours, hourId];
    onSelectionChange(newSelectedHours);
  };

  const handleSelectAllToggle = () => {
    if (isAllSelected) {
      onSelectionChange([]);
    } else {
      onSelectionChange(ALL_HOURS.map((h) => h.id));
    }
  };

  const handlePresetToggle = (preset: (typeof TIME_PRESETS)[0]) => {
    const allPresetSelected = preset.hours.every((hour) =>
      selectedHours.includes(hour)
    );

    if (allPresetSelected) {
      // Remove all preset hours
      onSelectionChange(
        selectedHours.filter((hour) => !preset.hours.includes(hour))
      );
    } else {
      // Add all preset hours
      const newHours = [...new Set([...selectedHours, ...preset.hours])];
      onSelectionChange(newHours);
    }
  };

  const isPresetSelected = (preset: (typeof TIME_PRESETS)[0]) => {
    return preset.hours.every((hour) => selectedHours.includes(hour));
  };

  return (
    <FilterCard
      title="時間帯"
      icon={icon}
      iconBgColor={iconBgColor}
      collapsible={collapsible}
      defaultExpanded={defaultExpanded}>
      <div className="space-y-4">
        {/* Select All Option */}
        <div className="flex items-center space-x-2 p-2 hover:bg-slate-50 rounded-lg transition-colors duration-200 group">
          <Checkbox
            id="select-all-hours"
            checked={isAllSelected}
            onCheckedChange={handleSelectAllToggle}
            className="data-[state=checked]:bg-orange-500 data-[state=checked]:border-orange-500"
          />
          <Label
            htmlFor="select-all-hours"
            className="text-sm font-medium text-slate-700 group-hover:text-slate-900 cursor-pointer">
            すべて ({selectedHours.length}/24)
          </Label>
        </div>

        {/* Time Period Presets */}
        <div className="space-y-2">
          <div className="text-xs font-medium text-slate-600 mb-2">
            クイック選択:
          </div>
          <div className="grid grid-cols-2 gap-2">
            {TIME_PRESETS.map((preset) => (
              <button
                key={preset.id}
                onClick={() => handlePresetToggle(preset)}
                className={`p-2 rounded-lg text-xs font-medium transition-all duration-200 ${
                  isPresetSelected(preset)
                    ? "bg-orange-100 text-orange-700 border border-orange-300"
                    : "bg-slate-50 text-slate-600 border border-slate-200 hover:bg-slate-100"
                }`}>
                {preset.label}
              </button>
            ))}
          </div>
        </div>

        {/* Individual Hours */}
        <div>
          <div className="text-xs font-medium text-slate-600 mb-2">
            個別選択:
          </div>
          <ScrollArea className="h-32 bg-slate-50 rounded-lg p-2 border border-slate-200">
            <div className="grid grid-cols-3 gap-1 pr-3">
              {ALL_HOURS.map((hour) => (
                <div
                  key={hour.id}
                  className="flex items-center space-x-2 p-1 hover:bg-white rounded transition-colors duration-200 group">
                  <Checkbox
                    id={`hour-${hour.id}`}
                    checked={selectedHours.includes(hour.id)}
                    onCheckedChange={() => handleHourToggle(hour.id)}
                    className="data-[state=checked]:bg-orange-500 data-[state=checked]:border-orange-500"
                  />
                  <Label
                    htmlFor={`hour-${hour.id}`}
                    className="text-xs text-slate-600 group-hover:text-slate-800 cursor-pointer transition-colors whitespace-nowrap">
                    {hour.label}
                  </Label>
                </div>
              ))}
            </div>
          </ScrollArea>
        </div>
      </div>
    </FilterCard>
  );
}
