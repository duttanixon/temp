"use client";

import React, { useState, useEffect } from "react";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { FilterCard } from "./FilterCard";

const ALL_GENDERS = [
  { id: "male", label: "男性" },
  { id: "female", label: "女性" },
];

interface GenderFilterProps {
  initialSelectedGenders?: string[];
  onSelectionChange?: (selectedGenders: string[]) => void;
}

export function GenderFilter({ initialSelectedGenders, onSelectionChange }: GenderFilterProps) {
  const [selectedGenders, setSelectedGenders] = useState<string[]>(initialSelectedGenders || ALL_GENDERS.map(g => g.id));
  const [isAllSelected, setIsAllSelected] = useState(selectedGenders.length === ALL_GENDERS.length);

  useEffect(() => {
    setIsAllSelected(selectedGenders.length === ALL_GENDERS.length);
    if (onSelectionChange) {
      onSelectionChange(selectedGenders);
    }
  }, [selectedGenders, onSelectionChange]);

  const handleGenderToggle = (genderId: string) => {
    setSelectedGenders((prevSelected) =>
      prevSelected.includes(genderId)
        ? prevSelected.filter((g) => g !== genderId)
        : [...prevSelected, genderId]
    );
  };

  const handleSelectAllToggle = () => {
    if (isAllSelected) {
      setSelectedGenders([]);
    } else {
      setSelectedGenders(ALL_GENDERS.map(g => g.id));
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
          />
          <Label htmlFor="select-all-genders" className="text-sm font-medium">
            すべて
          </Label>
        </div>
        {ALL_GENDERS.map((gender) => (
          <div key={gender.id} className="flex items-center space-x-2">
            <Checkbox
              id={gender.id}
              checked={selectedGenders.includes(gender.id)}
              onCheckedChange={() => handleGenderToggle(gender.id)}
            />
            <Label htmlFor={gender.id} className="text-sm font-normal">
              {gender.label}
            </Label>
          </div>
        ))}
      </div>
    </FilterCard>
  );
}