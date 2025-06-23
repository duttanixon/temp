"use client";

import { DatePickerWithRange } from "@/components/ui/date-range-picker";
import React from "react";
import { DateRange } from "react-day-picker";
import { FilterCard } from "./FilterCard";
import { format } from "date-fns";
import { ja } from "date-fns/locale";

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
  const formatPeriodSummary = (dateRange: DateRange | undefined): string => {
    if (!dateRange?.from) {
      return "未定義";
    }
    if (!dateRange.to) {
      return format(dateRange.from, "yyyy/M/d", { locale: ja });
    }
    return `${format(dateRange.from, "yyyy/M/d", { locale: ja })} - ${format(dateRange?.to, "yyyy/M/d", { locale: ja })}`;
  };
  const PeriodSummary = formatPeriodSummary(currentDateRange);

  return (
    <FilterCard
      title="比較対象期間"
      icon={icon}
      iconBgColor={iconBgColor}
      collapsible={collapsible}
      defaultExpanded={defaultExpanded}
      selectionSummary={PeriodSummary}
    >
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
