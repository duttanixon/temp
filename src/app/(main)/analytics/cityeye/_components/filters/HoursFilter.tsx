"use client";

import React, { useState, useEffect } from "react";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { FilterCard } from "./FilterCard";
import { ScrollArea } from "@/components/ui/scroll-area";

const ALL_HOURS = Array.from({ length: 24 }, (_, i) => ({
  id: `${String(i).padStart(2, '0')}:00`,
  label: `${String(i).padStart(2, '0')}:00`,
}));

interface HoursFilterProps {
  initialSelectedHours?: string[];
  onSelectionChange?: (selectedHours: string[]) => void;
}

export function HoursFilter({ initialSelectedHours, onSelectionChange }: HoursFilterProps) {
  const [selectedHours, setSelectedHours] = useState<string[]>(initialSelectedHours || ALL_HOURS.map(h => h.id));
  const [isAllSelected, setIsAllSelected] = useState(selectedHours.length === ALL_HOURS.length);

  useEffect(() => {
    setIsAllSelected(selectedHours.length === ALL_HOURS.length);
    if (onSelectionChange) {
      onSelectionChange(selectedHours);
    }
  }, [selectedHours, onSelectionChange]);

  const handleHourToggle = (hourId: string) => {
    setSelectedHours((prevSelected) =>
      prevSelected.includes(hourId)
        ? prevSelected.filter((h) => h !== hourId)
        : [...prevSelected, hourId]
    );
  };

  const handleSelectAllToggle = () => {
    if (isAllSelected) {
      setSelectedHours([]);
    } else {
      setSelectedHours(ALL_HOURS.map(h => h.id));
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
                  id={hour.id}
                  checked={selectedHours.includes(hour.id)}
                  onCheckedChange={() => handleHourToggle(hour.id)}
                />
                <Label htmlFor={hour.id} className="text-sm font-normal whitespace-nowrap">
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