// src/app/(main)/analytics/cityeye/_components/filters/ComparisonPeriodFilter.tsx
"use client";

import React, { useState } from "react";
import { DateRange } from "react-day-picker";
import { DatePickerWithRange } from "@/components/ui/date-range-picker";
import { FilterCard } from "./FilterCard";
import { subDays } from "date-fns";

interface ComparisonPeriodFilterProps {
  initialDateRange?: DateRange;
  onDateChange?: (dateRange: DateRange | undefined) => void;
  disabled?: boolean;
}

export function ComparisonPeriodFilter({ initialDateRange, onDateChange, disabled }: ComparisonPeriodFilterProps) {
  const [date, setDate] = useState<DateRange | undefined>(
    initialDateRange || {
      from: subDays(new Date(), 14),
      to: subDays(new Date(), 8),
    }
  );

  const handleDateChange = (newDate: DateRange | undefined) => {
    setDate(newDate);
    if (onDateChange) {
      onDateChange(newDate);
    }
  };

  return (
    <FilterCard title="比較表示対象期間">
      <DatePickerWithRange date={date} setDate={setDate} />
       {disabled && <div className="absolute inset-0 bg-gray-100 opacity-50 cursor-not-allowed" />}
    </FilterCard>
  );
}