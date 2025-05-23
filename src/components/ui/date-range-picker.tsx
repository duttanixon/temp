"use client";

import * as React from "react";
import { addDays, format, subDays, startOfMonth, endOfMonth, subMonths } from "date-fns";
import { CalendarIcon } from "lucide-react";
import { DateRange } from "react-day-picker";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

interface DatePickerWithRangeProps extends React.HTMLAttributes<HTMLDivElement> {
  date: DateRange | undefined;
  setDate: React.Dispatch<React.SetStateAction<DateRange | undefined>>;
  className?: string;
}

export function DatePickerWithRange({
  date,
  setDate,
  className,
}: DatePickerWithRangeProps) {
  // Define static ranges
  const staticRanges = [
    {
      label: "Today",
      onClick: () => {
        const today = new Date();
        setDate({ from: today, to: today });
      },
    },
    {
      label: "Yesterday",
      onClick: () => {
        const yesterday = subDays(new Date(), 1);
        setDate({ from: yesterday, to: yesterday });
      },
    },
    {
      label: "Last 7 Days",
      onClick: () => {
        setDate({
          from: subDays(new Date(), 6),
          to: new Date(),
        });
      },
    },
    {
      label: "Last 30 Days",
      onClick: () => {
        setDate({
          from: subDays(new Date(), 29),
          to: new Date(),
        });
      },
    },
    {
      label: "This Month",
      onClick: () => {
        const now = new Date();
        setDate({
          from: startOfMonth(now),
          to: endOfMonth(now),
        });
      },
    },
    {
      label: "Last Month",
      onClick: () => {
        const lastMonth = subMonths(new Date(), 1);
        setDate({
          from: startOfMonth(lastMonth),
          to: endOfMonth(lastMonth),
        });
      },
    },
  ];

  return (
    <div className={cn("grid gap-2", className)}>
      <Popover>
        <PopoverTrigger asChild>
          <Button
            id="date"
            variant={"outline"}
            className={cn(
              "w-[300px] justify-start text-left font-normal",
              !date && "text-muted-foreground"
            )}
          >
            <CalendarIcon className="mr-2 h-4 w-4" />
            {date?.from ? (
              date.to ? (
                <>
                  {format(date.from, "LLL dd, y")} -{" "}
                  {format(date.to, "LLL dd, y")}
                </>
              ) : (
                format(date.from, "LLL dd, y")
              )
            ) : (
              <span>Pick a date</span>
            )}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          <div className="flex p-3 bg-muted/20 border-b gap-2 flex-wrap">
            {staticRanges.map((range) => (
              <Button
                key={range.label}
                variant="outline"
                size="sm"
                onClick={range.onClick}
                className="text-xs"
              >
                {range.label}
              </Button>
            ))}
          </div>
          <Calendar
            initialFocus
            mode="range"
            defaultMonth={date?.from}
            selected={date}
            onSelect={setDate}
            numberOfMonths={2}
            className="p-3"
          />
        </PopoverContent>
      </Popover>
    </div>
  );
}