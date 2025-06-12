"use client";

import { DatePickerWithRange } from "@/components/ui/date-range-picker";
import React from "react";
import { DateRange } from "react-day-picker";
import { FilterCard } from "./FilterCard";

interface ComparisonPeriodFilterProps {
  currentDateRange: DateRange | undefined;
  onDateChange: React.Dispatch<React.SetStateAction<DateRange | undefined>>;
  disabled?: boolean;
  icon?: React.ReactNode;
  iconBgColor?: string;
  collapsible?: boolean;
  defaultExpanded?: boolean;
}

export function ComparisonPeriodFilter({
  currentDateRange,
  onDateChange,
  disabled,
  icon,
  iconBgColor,
  collapsible = false,
  defaultExpanded = true,
}: ComparisonPeriodFilterProps) {
  const formatDateRange = (dateRange?: DateRange) => {
    if (!dateRange?.from) return "比較期間を選択してください";
    if (!dateRange.to) return dateRange.from.toLocaleDateString("ja-JP");
    return `${dateRange.from.toLocaleDateString("ja-JP")} - ${dateRange.to.toLocaleDateString("ja-JP")}`;
  };

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
