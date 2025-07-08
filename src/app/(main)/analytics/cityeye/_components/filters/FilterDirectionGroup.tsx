"use client";

import { CityEyeFilterState } from "@/types/cityeye/cityEyeAnalytics";
import { Calendar, CalendarDays, Car, MapPin, Users } from "lucide-react";
import React, { useState, useEffect } from "react";
import { AnalysisPeriodDirectionFilter } from "./AnalysisPeriodDirectionFilter";
import { DaysFilter } from "./DaysFilter";
import { DevicesDirectionFilter } from "./DevicesDirectionFilter";
import { CustomerFilter } from "@/app/(main)/analytics/cityeye/_components/filters/CustomerFilter";
import { useSession } from "next-auth/react";
import { TrafficFilter } from "@/app/(main)/analytics/cityeye/_components/filters/TrafficFilter";

interface FilterDirectionGroupProps {
  horizontalTab: string;
  solutionId: string;
  currentFilters: CityEyeFilterState;
  onFilterChange: (newFilterValues: Partial<CityEyeFilterState>) => void;
}

export function FilterDirectionGroup({
  horizontalTab,
  solutionId,
  currentFilters,
  onFilterChange,
}: FilterDirectionGroupProps) {
  const showTrafficFilters = horizontalTab === "traffic-direction";

  const { data: session } = useSession();
  const userRole = session?.user?.role;
  const userCustomerId = session?.user?.customerId;

  // analysisPeriodDirection: Date[] を直接stateとして管理
  const [selectedDates, setSelectedDates] = useState<Date[]>(
    currentFilters.dates ?? []
  );

  useEffect(() => {
    setSelectedDates(currentFilters.dates ?? []);
  }, [currentFilters.dates]);

  // 日付選択変更時にanalysisPeriodDirectionを更新
  const handleDateChange = (dates: Date[]) => {
    setSelectedDates(dates);
    onFilterChange({ dates: dates });
  };

  console.log("FilterDirectionGroup currentFilters:", currentFilters);

  return (
    <div className="bg-gradient-to-br from-slate-50 to-white flex flex-col gap-3">
      <div className="space-y-4">
        <AnalysisPeriodDirectionFilter
          selectedDates={selectedDates ?? []}
          onDateChange={handleDateChange}
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
        {showTrafficFilters && (
          <TrafficFilter
            selectedTrafficTypes={currentFilters.selectedTrafficTypes}
            onSelectionChange={(newTrafficTypes) =>
              onFilterChange({ selectedTrafficTypes: newTrafficTypes })
            }
            icon={<Car className="w-4 h-4 text-blue-600" />}
            iconBgColor="bg-blue-100 group-hover:bg-blue-200"
            collapsible={true}
            defaultExpanded={false}
          />
        )}
      </div>
    </div>
  );
}
