"use client";

import { DatePickerWithRange } from "@/components/ui/date-range-picker";
import React from "react";
import { DateRange } from "react-day-picker";
import { FilterCard } from "./FilterCard";

interface ComparisonPeriodFilterProps {
  currentDateRange: DateRange | undefined;
  onDateChange: React.Dispatch<React.SetStateAction<DateRange | undefined>>;
  icon?: React.ReactNode;
  iconBgColor?: string;
  collapsible?: boolean;
  defaultExpanded?: boolean;
}

export function ComparisonPeriodFilter({
  currentDateRange,
  onDateChange,
  icon,
  iconBgColor,
  collapsible = false,
  defaultExpanded = true,
}: ComparisonPeriodFilterProps) {
  return (
    <FilterCard
      title="比較対象期間"
      icon={icon}
      iconBgColor={iconBgColor}
      collapsible={collapsible}
      defaultExpanded={defaultExpanded}>
      <div className="p-3 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors duration-200">
        <DatePickerWithRange
          date={currentDateRange}
          setDate={onDateChange}
          childClassName="w-full"
        />
      </div>
    </FilterCard>
  );
}
