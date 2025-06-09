"use client";

import React from "react"; // Removed useState, useEffect
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { FilterCard } from "./FilterCard";

const ALL_GENDERS = [
  { id: "male", label: "男性" },
  { id: "female", label: "女性" },
];

interface GenderFilterProps {
  selectedGenders: string[];
  onSelectionChange: (selectedGenders: string[]) => void;
}

export function GenderFilter({
  selectedGenders,
  onSelectionChange,
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
    <FilterCard title="性別">
      <div className="space-y-2">
        <div className="flex items-center space-x-2">
          <Checkbox
            id="select-all-genders"
            checked={isAllSelected}
            onCheckedChange={handleSelectAllToggle}
            className="cursor-pointer"
          />
          <Label
            htmlFor="select-all-genders"
            className="text-sm font-medium cursor-pointer"
          >
            すべて
          </Label>
        </div>
        {ALL_GENDERS.map((gender) => (
          <div key={gender.id} className="flex items-center space-x-2">
            <Checkbox
              id={`gender-${gender.id}`}
              checked={selectedGenders.includes(gender.id)}
              onCheckedChange={() => handleGenderToggle(gender.id)}
              className="cursor-pointer"
            />
            <Label
              htmlFor={`gender-${gender.id}`}
              className="text-sm font-normal cursor-pointer"
            >
              {gender.label}
            </Label>
          </div>
        ))}
      </div>
    </FilterCard>
  );
}
