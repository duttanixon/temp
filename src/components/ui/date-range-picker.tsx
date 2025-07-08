"use client";

import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { cn } from "@/lib/utils";
import { endOfMonth, format, startOfMonth, subDays, subMonths } from "date-fns";
import { CalendarIcon } from "lucide-react";
import { DateRange } from "react-day-picker";
import { toast } from "sonner";

interface DatePickerWithRangeProps
  extends React.HTMLAttributes<HTMLDivElement> {
  date: DateRange | undefined;
  setDate: React.Dispatch<React.SetStateAction<DateRange | undefined>>;
  className?: string;
  childClassName?: string;
}
interface DatePickerWithMultipleProps
  extends React.HTMLAttributes<HTMLDivElement> {
  dates: Date[];
  setDates: React.Dispatch<React.SetStateAction<Date[]>>;
  className?: string;
  childClassName?: string;
  maxSelectable?: number;
}

export function DatePickerWithRange({
  date,
  setDate,
  className,
  childClassName,
}: DatePickerWithRangeProps) {
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
              "w-[300px] justify-start text-left font-normal cursor-pointer",
              childClassName,
              !date && "text-muted-foreground"
            )}
          >
            <CalendarIcon className="mr-2 size-4" />
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
                className="text-xs cursor-pointer"
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

export function DatePickerWithMultiple({
  dates,
  setDates,
  className,
  childClassName,
  maxSelectable = 7,
}: DatePickerWithMultipleProps) {
  const staticRanges = [
    {
      label: "Today",
      onClick: () => {
        const today = new Date();
        setDates([today]);
      },
    },
    {
      label: "Yesterday",
      onClick: () => {
        const today = new Date();
        const yesterday = subDays(today, 1);
        setDates([yesterday, today]);
      },
    },
    {
      label: "Last 7 Days",
      onClick: () => {
        const today = new Date();
        const days = Array.from({ length: 7 }, (_, i) => subDays(today, 6 - i));
        setDates(days);
      },
    },
  ];
  const handleSelect = (selected: Date[] | undefined) => {
    if (!selected) {
      setDates([]);
      return;
    }
    if (selected.length > maxSelectable) {
      toast.error(`最大${maxSelectable}日まで選択できます。`);
      return;
    }
    setDates(selected);
  };
  return (
    <div className={cn("grid gap-2", className)}>
      <Popover>
        <PopoverTrigger asChild>
          <Button
            id="date"
            variant={"outline"}
            className={cn(
              "w-[300px] justify-start text-left font-normal overflow-x-auto cursor-pointer",
              childClassName,
              (!dates || dates.length === 0) && "text-muted-foreground"
            )}
          >
            <CalendarIcon className="mr-2 size-4" />
            {dates && dates.length > 0 ? (
              dates.map((d) => format(d, "LLL dd, y")).join(", ")
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
                className="text-xs cursor-pointer"
              >
                {range.label}
              </Button>
            ))}
          </div>
          <Calendar
            initialFocus
            mode="multiple"
            selected={dates}
            onSelect={handleSelect}
            numberOfMonths={2}
            className="p-3"
          />
        </PopoverContent>
      </Popover>
    </div>
  );
}
