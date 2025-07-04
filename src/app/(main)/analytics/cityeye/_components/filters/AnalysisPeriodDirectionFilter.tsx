"use client";

import { DatePickerWithMultiple } from "@/components/ui/date-range-picker";
import React from "react";
import { FilterCard } from "./FilterCard";
import { format } from "date-fns";
import { ja } from "date-fns/locale";

interface AnalysisPeriodDirectionFilterProps {
  selectedDates: Date[];
  onDateChange: (dates: Date[]) => void;
  limitDays?: number;
  icon?: React.ReactNode;
  iconBgColor?: string;
  collapsible?: boolean;
  defaultExpanded?: boolean;
}

export function AnalysisPeriodDirectionFilter({
  selectedDates,
  onDateChange,
  limitDays,
  icon,
  iconBgColor,
  collapsible = false,
  defaultExpanded = true,
}: AnalysisPeriodDirectionFilterProps) {
  const formatPeriodSummary = (dates: Date[]): string => {
    if (!dates || dates.length === 0) {
      return "未定義";
    }
    const sorted = [...dates].sort((a, b) => a.getTime() - b.getTime());
    return sorted.map((d) => format(d, "yyyy/M/d", { locale: ja })).join(", ");
  };
  const PeriodSummary = formatPeriodSummary(selectedDates);

  const handleDateChange = (value: Date[] | ((prev: Date[]) => Date[])) => {
    // setStateの関数型は来ない想定だが、型安全のため分岐
    if (typeof value === "function") {
      // prevStateを使う場合は空配列を渡す（通常運用では来ない）
      onDateChange([]);
    } else {
      onDateChange(value);
    }
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
        <DatePickerWithMultiple
          dates={selectedDates}
          setDates={handleDateChange}
          childClassName="w-full"
          maxSelectable={limitDays ?? 7}
        />
        <span className="text-xs text-gray-500 mt-2">
          選択可能な期間は最大{limitDays}日です。
        </span>
      </div>
    </FilterCard>
  );
}
