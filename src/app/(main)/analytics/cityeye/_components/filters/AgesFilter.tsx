"use client";

import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import React from "react";
import { FilterCard } from "./FilterCard";

const ALL_AGES = [
  { id: "under_18", label: "18歳未満" },
  { id: "18_to_29", label: "18-29歳" },
  { id: "30_to_49", label: "30-49歳" },
  { id: "50_to_64", label: "50-64歳" },
  { id: "over_64", label: "65歳以上" },
];

interface AgesFilterProps {
  selectedAges: string[];
  onSelectionChange: (selectedAges: string[]) => void;
  icon?: React.ReactNode;
  iconBgColor?: string;
  collapsible?: boolean;
  defaultExpanded?: boolean;
}

export function AgesFilter({
  selectedAges,
  onSelectionChange,
  icon,
  iconBgColor,
  collapsible = false,
  defaultExpanded = true,
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
    <FilterCard
      title="年齢層"
      icon={icon}
      iconBgColor={iconBgColor}
      collapsible={collapsible}
      defaultExpanded={defaultExpanded}>
      <div className="space-y-3">
        {/* Select All Option */}
        <div className="flex items-center space-x-2 p-1 hover:bg-slate-50 rounded-lg transition-colors duration-200 group">
          <Checkbox
            id="select-all-ages"
            checked={isAllSelected}
            onCheckedChange={handleSelectAllToggle}
            className="data-[state=checked]:bg-indigo-500 data-[state=checked]:border-indigo-500"
          />
          <Label
            htmlFor="select-all-ages"
            className="text-sm font-medium text-slate-700 group-hover:text-slate-900 cursor-pointer">
            すべて ({selectedAges.length}/{ALL_AGES.length})
          </Label>
        </div>

        {/* Individual Age Options */}
        <div>
          <div className="text-xs text-slate-500 font-medium mb-2">
            個別選択:
          </div>
          <div className="grid grid-cols-2 gap-1">
            {ALL_AGES.map((age) => (
              <div
                key={age.id}
                className="flex items-center space-x-2 p-1 hover:bg-slate-50 rounded-lg transition-colors duration-200 group">
                <Checkbox
                  id={`age-${age.id}`}
                  checked={selectedAges.includes(age.id)}
                  onCheckedChange={() => handleAgeToggle(age.id)}
                  className="cursor-pointer data-[state=checked]:bg-indigo-500 data-[state=checked]:border-indigo-500"
                />
                <Label
                  htmlFor={`age-${age.id}`}
                  className="text-sm text-slate-600 group-hover:text-slate-800 cursor-pointer transition-colors">
                  {age.label}
                </Label>
              </div>
            ))}
          </div>
        </div>
      </div>
    </FilterCard>
  );
}
