"use client";

import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import React from "react";
import { FilterCard } from "./FilterCard";

const ALL_GENDERS = [
  { id: "male", label: "男性" },
  { id: "female", label: "女性" },
];

interface GenderFilterProps {
  selectedGenders: string[];
  onSelectionChange: (selectedGenders: string[]) => void;
  icon?: React.ReactNode;
  iconBgColor?: string;
  collapsible?: boolean;
  defaultExpanded?: boolean;
}

export function GenderFilter({
  selectedGenders,
  onSelectionChange,
  icon,
  iconBgColor,
  collapsible = false,
  defaultExpanded = true,
}: GenderFilterProps) {
  const isAllSelected =
    ALL_GENDERS.length > 0 && selectedGenders.length === ALL_GENDERS.length;

  const handleGenderToggle = (genderId: string) => {
    const newSelectedGenders = selectedGenders.includes(genderId)
      ? selectedGenders.filter((g) => g !== genderId)
      : [...selectedGenders, genderId];
    onSelectionChange(newSelectedGenders);
  };

  const handleSelectAllToggle = () => {
    if (isAllSelected) {
      onSelectionChange([]);
    } else {
      onSelectionChange(ALL_GENDERS.map((g) => g.id));
    }
  };

  return (
    <FilterCard
      title="性別"
      icon={icon}
      iconBgColor={iconBgColor}
      collapsible={collapsible}
      defaultExpanded={defaultExpanded}>
      <div className="space-y-3">
        {/* Select All Option */}
        <div className="flex items-center space-x-2 p-1 hover:bg-slate-50 rounded-lg transition-colors duration-200 group">
          <Checkbox
            id="select-all-genders"
            checked={isAllSelected}
            onCheckedChange={handleSelectAllToggle}
            className="data-[state=checked]:bg-pink-500 data-[state=checked]:border-pink-500"
          />
          <Label
            htmlFor="select-all-genders"
            className="text-sm font-medium text-slate-700 group-hover:text-slate-900 cursor-pointer">
            すべて ({selectedGenders.length}/{ALL_GENDERS.length})
          </Label>
        </div>

        {/* Individual Gender Options */}
        <div>
          <div className="text-xs text-slate-500 font-medium mb-2">
            個別選択:
          </div>
          <div className="flex gap-2">
            {ALL_GENDERS.map((gender) => (
              <div
                key={gender.id}
                className="flex items-center space-x-2 p-1 hover:bg-slate-50 rounded-lg transition-colors duration-200 group">
                <Checkbox
                  id={`gender-${gender.id}`}
                  checked={selectedGenders.includes(gender.id)}
                  onCheckedChange={() => handleGenderToggle(gender.id)}
                  className="data-[state=checked]:bg-pink-500 data-[state=checked]:border-pink-500"
                />
                <Label
                  htmlFor={`gender-${gender.id}`}
                  className="text-sm text-slate-600 group-hover:text-slate-800 cursor-pointer transition-colors">
                  {gender.label}
                </Label>
              </div>
            ))}
          </div>
        </div>
      </div>
    </FilterCard>
  );
}
