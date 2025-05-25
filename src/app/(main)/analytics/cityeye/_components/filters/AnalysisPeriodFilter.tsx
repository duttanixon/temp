"use client";

import React from "react";
import { DateRange } from "react-day-picker";
import { DatePickerWithRange } from "@/components/ui/date-range-picker";
import { FilterCard } from "./FilterCard";
// subDays is not used here anymore as initial state is managed by parent
// import { subDays } from "date-fns";

interface AnalysisPeriodFilterProps {
  currentDateRange: DateRange | undefined; // Changed from initialDateRange
  onDateChange: React.Dispatch<React.SetStateAction<DateRange | undefined>>;
}

export function AnalysisPeriodFilter({
  currentDateRange,
  onDateChange,
}: AnalysisPeriodFilterProps) {
  // The DatePickerWithRange component internally handles its presentation state.
  // We directly use the props for managing the selected date range.
  return (
    <FilterCard title="分析対象期間">
      <DatePickerWithRange date={currentDateRange} setDate={onDateChange} />
    </FilterCard>
  );
}
