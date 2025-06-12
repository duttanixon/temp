"use client";

import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import React from "react";
import { FilterCard } from "./FilterCard";

const ALL_DAYS = [
  { id: "monday", label: "月曜" },
  { id: "tuesday", label: "火曜" },
  { id: "wednesday", label: "水曜" },
  { id: "thursday", label: "木曜" },
  { id: "friday", label: "金曜" },
  { id: "saturday", label: "土曜" },
  { id: "sunday", label: "日曜" },
];

interface DaysFilterProps {
  selectedDays: string[];
  onSelectionChange: (selectedDays: string[]) => void;
  icon?: React.ReactNode;
  iconBgColor?: string;
  collapsible?: boolean;
  defaultExpanded?: boolean;
}

export function DaysFilter({
  selectedDays,
  onSelectionChange,
  icon,
  iconBgColor,
  collapsible = false,
  defaultExpanded = true,
}: DaysFilterProps) {
  const isAllSelected = ALL_DAYS.length === selectedDays.length;

  const handleDayToggle = (dayId: string) => {
    const newSelectedDays = selectedDays.includes(dayId)
      ? selectedDays.filter((d) => d !== dayId)
      : [...selectedDays, dayId];
    onSelectionChange(newSelectedDays);
  };

  const handleSelectAllToggle = () => {
    if (isAllSelected) {
      onSelectionChange([]);
    } else {
      onSelectionChange(ALL_DAYS.map((d) => d.id));
    }
  };

  // Quick select buttons for common day ranges
  const quickSelectRanges = [
    {
      label: "平日",
      days: ["monday", "tuesday", "wednesday", "thursday", "friday"],
    },
    { label: "週末", days: ["saturday", "sunday"] },
  ];

  const handleQuickSelect = (days: string[]) => {
    onSelectionChange(days);
  };

  return (
    <FilterCard
      title="曜日"
      icon={icon}
      iconBgColor={iconBgColor}
      collapsible={collapsible}
      defaultExpanded={defaultExpanded}>
      <div className="space-y-4">
        {/* Select All Option */}
        <div className="flex items-center space-x-2 p-2 hover:bg-slate-50 rounded-lg transition-colors duration-200 group">
          <Checkbox
            id="select-all-days"
            checked={isAllSelected}
            onCheckedChange={handleSelectAllToggle}
            className="data-[state=checked]:bg-blue-500 data-[state=checked]:border-blue-500"
          />
          <Label
            htmlFor="select-all-days"
            className="text-sm font-medium text-slate-700 group-hover:text-slate-900 cursor-pointer">
            すべて ({selectedDays.length}/7)
          </Label>
        </div>

        {/* Quick Select Buttons */}
        <div className="space-y-2">
          <div className="text-xs text-slate-500 font-medium">
            クイック選択:
          </div>
          <div className="grid grid-cols-2 gap-2">
            {quickSelectRanges.map((range) => (
              <button
                key={range.label}
                onClick={() => handleQuickSelect(range.days)}
                className="text-xs p-2 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-lg transition-colors duration-200 border border-blue-200 hover:border-blue-300">
                {range.label}
              </button>
            ))}
          </div>
        </div>

        {/* Individual Day Options */}
        <div>
          <div className="text-xs text-slate-500 font-medium mb-2">
            個別選択:
          </div>
          <div className="grid grid-cols-3 gap-1">
            {ALL_DAYS.map((day) => (
              <div
                key={day.id}
                className="flex items-center space-x-2 p-1 hover:bg-slate-50 rounded-lg transition-colors duration-200 group">
                <Checkbox
                  id={day.id}
                  checked={selectedDays.includes(day.id)}
                  onCheckedChange={() => handleDayToggle(day.id)}
                  className="data-[state=checked]:bg-blue-500 data-[state=checked]:border-blue-500"
                />
                <Label
                  htmlFor={day.id}
                  className="text-sm text-slate-600 group-hover:text-slate-800 cursor-pointer transition-colors">
                  {day.label}
                </Label>
              </div>
            ))}
          </div>
        </div>
      </div>
    </FilterCard>
  );
}
