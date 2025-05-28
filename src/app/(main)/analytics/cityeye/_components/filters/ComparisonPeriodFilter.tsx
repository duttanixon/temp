"use client";

import React from "react";
import { DateRange } from "react-day-picker";
import { DatePickerWithRange } from "@/components/ui/date-range-picker";
import { FilterCard } from "./FilterCard";
// subDays is not used here anymore
// import { subDays } from "date-fns";

interface ComparisonPeriodFilterProps {
  currentDateRange: DateRange | undefined; // Changed from initialDateRange
  onDateChange: React.Dispatch<React.SetStateAction<DateRange | undefined>>;
  disabled?: boolean;
}

export function ComparisonPeriodFilter({
  currentDateRange,
  onDateChange,
  disabled,
}: ComparisonPeriodFilterProps) {
  // Directly use props for date and callback
  // The disabled overlay is a good touch if the filter should be conditionally non-interactive.
  return (
    <FilterCard title="比較表示対象期間">
      <div className="relative">
        {" "}
        {/* Added relative positioning for the overlay */}
        <DatePickerWithRange date={currentDateRange} setDate={onDateChange} />
        {disabled && (
          <div className="absolute inset-0 bg-gray-100 bg-opacity-50 cursor-not-allowed z-10" />
        )}
      </div>
    </FilterCard>
  );
}
