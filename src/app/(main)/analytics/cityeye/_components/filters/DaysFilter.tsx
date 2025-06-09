"use client";

import React, { useState, useEffect } from "react";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
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
  selectedDays: string[]; // Receives current selection
  onSelectionChange: (selectedDays: string[]) => void; // Callback to update parent state
}

export function DaysFilter({
  selectedDays,
  onSelectionChange,
}: DaysFilterProps) {
  // isAllSelected can be derived or be local UI state for convenience
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

  return (
    <FilterCard title="曜日">
      <div className="space-y-2">
        <div className="flex items-center space-x-2">
          <Checkbox
            id="select-all-days"
            checked={isAllSelected}
            onCheckedChange={handleSelectAllToggle}
            className="cursor-pointer"
          />
          <Label
            htmlFor="select-all-days"
            className="text-sm font-medium cursor-pointer"
          >
            すべて
          </Label>
        </div>
        <div className="grid grid-cols-2 gap-2">
          {ALL_DAYS.map((day) => (
            <div key={day.id} className="flex items-center space-x-2">
              <Checkbox
                id={day.id}
                checked={selectedDays.includes(day.id)}
                onCheckedChange={() => handleDayToggle(day.id)}
                className="cursor-pointer"
              />
              <Label
                htmlFor={day.id}
                className="text-sm font-normal cursor-pointer"
              >
                {day.label}
              </Label>
            </div>
          ))}
        </div>
      </div>
    </FilterCard>
  );
}
