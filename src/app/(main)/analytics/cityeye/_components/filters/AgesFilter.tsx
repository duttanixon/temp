"use client";

import React from "react"; // Removed useState, useEffect as isAllSelected is derived
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { FilterCard } from "./FilterCard";

const ALL_AGES = [
  { id: "under_18", label: "18歳未満" }, // Matched to backend AnalyticsFilters
  { id: "18_to_29", label: "18-29歳" },
  { id: "30_to_49", label: "30-49歳" },
  { id: "50_to_64", label: "50-64歳" },
  { id: "over_64", label: "65歳以上" }, // Matched to backend AnalyticsFilters (maps to 65_plus on backend)
];

interface AgesFilterProps {
  selectedAges: string[];
  onSelectionChange: (selectedAges: string[]) => void;
}

export function AgesFilter({
  selectedAges,
  onSelectionChange,
}: AgesFilterProps) {
  const isAllSelected =
    ALL_AGES.length > 0 && selectedAges.length === ALL_AGES.length;

  const handleAgeToggle = (ageId: string) => {
    const newSelectedAges = selectedAges.includes(ageId)
      ? selectedAges.filter((a) => a !== ageId)
      : [...selectedAges, ageId];
    onSelectionChange(newSelectedAges);
  };

  const handleSelectAllToggle = () => {
    if (isAllSelected) {
      onSelectionChange([]);
    } else {
      onSelectionChange(ALL_AGES.map((a) => a.id));
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
            className="cursor-pointer"
          />
          <Label
            htmlFor="select-all-ages"
            className="text-sm font-medium cursor-pointer"
          >
            すべて
          </Label>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-x-2 gap-y-1">
          {ALL_AGES.map((age) => (
            <div key={age.id} className="flex items-center space-x-2">
              <Checkbox
                id={`age-${age.id}`}
                checked={selectedAges.includes(age.id)}
                onCheckedChange={() => handleAgeToggle(age.id)}
                className="cursor-pointer"
              />
              <Label
                htmlFor={`age-${age.id}`}
                className="text-sm font-normal whitespace-nowrap cursor-pointer"
              >
                {age.label}
              </Label>
            </div>
          ))}
        </div>
      </div>
    </FilterCard>
  );
}
