"use client";

import React, { useState, useEffect } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
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
  initialSelectedDays?: string[];
  onSelectionChange?: (selectedDays: string[]) => void;
}

export function DaysFilter({ initialSelectedDays, onSelectionChange }: DaysFilterProps) {
  const [selectedDays, setSelectedDays] = useState<string[]>(initialSelectedDays || ALL_DAYS.map(d => d.id));
  const [isAllSelected, setIsAllSelected] = useState(selectedDays.length === ALL_DAYS.length);

  useEffect(() => {
    setIsAllSelected(selectedDays.length === ALL_DAYS.length);
    if (onSelectionChange) {
      onSelectionChange(selectedDays);
    }
  }, [selectedDays, onSelectionChange]);

  const handleDayToggle = (dayId: string) => {
    setSelectedDays((prevSelected) =>
      prevSelected.includes(dayId)
        ? prevSelected.filter((d) => d !== dayId)
        : [...prevSelected, dayId]
    );
  };

  const handleSelectAllToggle = () => {
    if (isAllSelected) {
      setSelectedDays([]);
    } else {
      setSelectedDays(ALL_DAYS.map(d => d.id));
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
          />
          <Label htmlFor="select-all-days" className="text-sm font-medium">
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
              />
              <Label htmlFor={day.id} className="text-sm font-normal">
                {day.label}
              </Label>
            </div>
          ))}
        </div>
      </div>
    </FilterCard>
  );
}