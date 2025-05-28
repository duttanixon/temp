"use client";

import React, { useEffect, useState } from "react"; // Keep useState for isAllSelected if preferred
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { FilterCard } from "./FilterCard";
import { ScrollArea } from "@/components/ui/scroll-area";

const ALL_HOURS = Array.from({ length: 24 }, (_, i) => ({
  id: `${String(i).padStart(2, "0")}:00`,
  label: `${String(i).padStart(2, "0")}:00`,
}));

interface HoursFilterProps {
  selectedHours: string[]; // Changed from initialSelectedHours
  onSelectionChange: (selectedHours: string[]) => void;
}

export function HoursFilter({
  selectedHours,
  onSelectionChange,
}: HoursFilterProps) {
  // isAllSelected can be derived directly or use useState for minor optimization if list is huge.
  // For 24 items, direct derivation is fine.
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

  return (
    <FilterCard title="時間帯">
      <div className="space-y-2">
        <div className="flex items-center space-x-2">
          <Checkbox
            id="select-all-hours"
            checked={isAllSelected}
            onCheckedChange={handleSelectAllToggle}
          />
          <Label htmlFor="select-all-hours" className="text-sm font-medium">
            すべて
          </Label>
        </div>
        <ScrollArea className="h-32">
          <div className="grid grid-cols-2 gap-y-1 pr-3">
            {ALL_HOURS.map((hour) => (
              <div key={hour.id} className="flex items-center space-x-2">
                <Checkbox
                  id={`hour-${hour.id}`} // Ensure unique ID if ALL_HOURS.id might not be unique enough across page
                  checked={selectedHours.includes(hour.id)}
                  onCheckedChange={() => handleHourToggle(hour.id)}
                />
                <Label
                  htmlFor={`hour-${hour.id}`}
                  className="text-sm font-normal whitespace-nowrap"
                >
                  {hour.label}
                </Label>
              </div>
            ))}
          </div>
        </ScrollArea>
      </div>
    </FilterCard>
  );
}
