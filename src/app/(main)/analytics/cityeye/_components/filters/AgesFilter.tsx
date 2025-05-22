// src/app/(main)/analytics/cityeye/_components/filters/AgesFilter.tsx
"use client";

import React, { useState, useEffect } from "react";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { FilterCard } from "./FilterCard";

const ALL_AGES = [
  { id: "under18", label: "<18" },
  { id: "18-29", label: "18-29" },
  { id: "30-49", label: "30-49" },
  { id: "50-64", label: "50-64" },
  { id: "over64", label: ">64" },
];

interface AgesFilterProps {
  initialSelectedAges?: string[];
  onSelectionChange?: (selectedAges: string[]) => void;
}

export function AgesFilter({ initialSelectedAges, onSelectionChange }: AgesFilterProps) {
  const [selectedAges, setSelectedAges] = useState<string[]>(initialSelectedAges || ALL_AGES.map(a => a.id));
  const [isAllSelected, setIsAllSelected] = useState(selectedAges.length === ALL_AGES.length);

  useEffect(() => {
    setIsAllSelected(selectedAges.length === ALL_AGES.length);
    if (onSelectionChange) {
      onSelectionChange(selectedAges);
    }
  }, [selectedAges, onSelectionChange]);

  const handleAgeToggle = (ageId: string) => {
    setSelectedAges((prevSelected) =>
      prevSelected.includes(ageId)
        ? prevSelected.filter((a) => a !== ageId)
        : [...prevSelected, ageId]
    );
  };

  const handleSelectAllToggle = () => {
    if (isAllSelected) {
      setSelectedAges([]);
    } else {
      setSelectedAges(ALL_AGES.map(a => a.id));
    }
  };

  return (
    <FilterCard title="年齢層">
      <div className="space-y-2">
        <div className="flex items-center space-x-2">
          <Checkbox
            id="select-all-ages"
            checked={isAllSelected}
            onCheckedChange={handleSelectAllToggle}
          />
          <Label htmlFor="select-all-ages" className="text-sm font-medium">
            すべて
          </Label>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-x-2 gap-y-1">
          {ALL_AGES.map((age) => (
            <div key={age.id} className="flex items-center space-x-2">
              <Checkbox
                id={age.id}
                checked={selectedAges.includes(age.id)}
                onCheckedChange={() => handleAgeToggle(age.id)}
              />
              <Label htmlFor={age.id} className="text-sm font-normal whitespace-nowrap">
                {age.label}
              </Label>
            </div>
          ))}
        </div>
      </div>
    </FilterCard>
  );
}