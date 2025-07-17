"use client";

import { DatePickerWithRange } from "@/components/ui/date-range-picker";
import React from "react";
import { DateRange } from "react-day-picker";
import { FilterCard } from "./FilterCard";
import { format } from "date-fns";
import { ja } from "date-fns/locale";

interface AnalysisPeriodFilterProps {
  currentDateRange: DateRange | undefined;
  onDateChange: React.Dispatch<React.SetStateAction<DateRange | undefined>>;
  limitDays?: number;
  icon?: React.ReactNode;
  iconBgColor?: string;
  collapsible?: boolean;
  defaultExpanded?: boolean;
}

export function AnalysisPeriodFilter({
  currentDateRange,
  onDateChange,
  limitDays,
  icon,
  iconBgColor,
  collapsible = false,
  defaultExpanded = true,
}: AnalysisPeriodFilterProps) {
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

  const handleDateChange: React.Dispatch<
    React.SetStateAction<DateRange | undefined>
  > = (value) => {
    // If value is a function, resolve it to get the next state
    const nextRange =
      typeof value === "function" ? value(currentDateRange) : value;

    if (limitDays && nextRange?.from && nextRange.to) {
      const diff =
        (nextRange.to.getTime() - nextRange.from.getTime()) /
          (1000 * 60 * 60 * 24) +
        1;
      if (diff > limitDays) {
        alert(`期間は${limitDays}日以内に設定してください。`);
        return;
      }
    }
    onDateChange(value);
  };

  return (
    <FilterCard
      title="分析対象期間"
      icon={icon}
      iconBgColor={iconBgColor}
      collapsible={collapsible}
      defaultExpanded={defaultExpanded}
      selectionSummary={PeriodSummary}
    >
      <div className="p-3 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors duration-200">
        <DatePickerWithRange
          date={currentDateRange}
          setDate={handleDateChange}
          childClassName="w-full"
        />
      </div>
    </FilterCard>
  );
}
