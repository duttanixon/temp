"use client";

import { CityEyeFilterState } from "@/types/cityeye/cityEyeAnalytics";
import { Calendar, CalendarDays, MapPin, Users } from "lucide-react";
import React from "react";
import { DateRange } from "react-day-picker";
import { AnalysisPeriodFilter } from "./AnalysisPeriodFilter";
import { DaysFilter } from "./DaysFilter";
import { DevicesDirectionFilter } from "./DevicesDirectionFilter";
import { CustomerFilter } from "@/app/(main)/analytics/cityeye/_components/filters/CustomerFilter";
import { useSession } from "next-auth/react";

interface FilterDirectionGroupProps {
  solutionId: string;
  currentFilters: CityEyeFilterState;
  onFilterChange: (newFilterValues: Partial<CityEyeFilterState>) => void;
}

export function FilterDirectionGroup({
  solutionId,
  currentFilters,
  onFilterChange,
}: FilterDirectionGroupProps) {
  const { data: session } = useSession();
  const userRole = session?.user?.role;
  const userCustomerId = session?.user?.customerId;

  // Create correctly typed handlers for date changes
  const handleAnalysisPeriodChange: React.Dispatch<
    React.SetStateAction<DateRange | undefined>
  > = (value) => {
    const newDate =
      typeof value === "function"
        ? value(currentFilters.analysisPeriod)
        : value;
    onFilterChange({ analysisPeriod: newDate });
  };

  // useEffect(() => {
  //   onFilterChange({ selectedDevices: [] });
  // }, [currentFilters.selectedCustomers, solutionId]);

  console.log("FilterGroup currentFilters:", currentFilters);

  return (
    <div className="bg-gradient-to-br from-slate-50 to-white flex flex-col gap-3">
      <div className="space-y-4">
        <AnalysisPeriodFilter
          currentDateRange={currentFilters.analysisPeriod}
          onDateChange={handleAnalysisPeriodChange}
          icon={<CalendarDays className="w-4 h-4 text-blue-600" />}
          iconBgColor="bg-blue-100 group-hover:bg-blue-200"
          collapsible={true}
          defaultExpanded={false}
          limitDays={7}
        />

        <DaysFilter
          selectedDays={currentFilters.selectedDays}
          onSelectionChange={(newDays) =>
            onFilterChange({ selectedDays: newDays })
          }
          icon={<Calendar className="w-4 h-4 text-blue-600" />}
          iconBgColor="bg-blue-100 group-hover:bg-blue-200"
          collapsible={true}
          defaultExpanded={false}
        />
        {userRole === "ADMIN" && (
          <CustomerFilter
            selectedCustomers={currentFilters.selectedCustomers}
            onSelectionChange={(newCustomers) =>
              onFilterChange({ selectedCustomers: newCustomers })
            }
            icon={<Users className="w-4 h-4 text-blue-600" />}
            iconBgColor="bg-blue-100 group-hover:bg-blue-200"
            collapsible={true}
            defaultExpanded={false}
          />
        )}

        <DevicesDirectionFilter
          solutionId={solutionId}
          selectedDevices={currentFilters.selectedDevices}
          onSelectionChange={(newDevices) =>
            onFilterChange({ selectedDevices: newDevices })
          }
          customerId={currentFilters.selectedCustomers}
          userCustomerId={userCustomerId}
          icon={<MapPin className="w-4 h-4 text-blue-600" />}
          iconBgColor="bg-blue-100 group-hover:bg-blue-200"
          collapsible={true}
          defaultExpanded={false}
        />
      </div>
    </div>
  );
}
