"use client";

import React, { useState }  from "react";
import { DateRange } from "react-day-picker";
import { DatePickerWithRange } from "@/components/ui/date-range-picker";
import { FilterCard } from "./FilterCard";
import { subDays } from "date-fns";

interface AnalysisPeriodFilterProps {
  initialDateRange?: DateRange;
  onDateChange?: (dateRange: DateRange | undefined) => void;
}

export function AnalysisPeriodFilter({ initialDateRange, onDateChange }: AnalysisPeriodFilterProps) {
  const [date, setDate] = useState<DateRange | undefined>(
    initialDateRange || {
      from: subDays(new Date(), 7),
      to: new Date(),
    }
  );

  return (
    <FilterCard title="分析対象期間">
      <DatePickerWithRange date={date} setDate={setDate} />
    </FilterCard>
  );
}