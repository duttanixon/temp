"use client";

import { CityEyeFilterState } from "@/types/cityeye/cityEyeAnalytics";
import {
  Calendar,
  CalendarDays,
  Car,
  Clock,
  MapPin,
  User,
  Users,
} from "lucide-react";
import React from "react";
import { DateRange } from "react-day-picker";
import { AgesFilter } from "./AgesFilter";
import { AnalysisPeriodFilter } from "./AnalysisPeriodFilter";
import { ComparisonPeriodFilter } from "./ComparisonPeriodFilter";
import { DaysFilter } from "./DaysFilter";
import { DevicesFilter } from "./DevicesFilter";
import { GenderFilter } from "./GenderFilter";
import { HoursFilter } from "./HoursFilter";
import { TrafficFilter } from "./TrafficFilter";

interface FilterGroupProps {
  verticalTab: string;
  horizontalTab: string;
  solutionId: string;
  currentFilters: CityEyeFilterState;
  onFilterChange: (newFilterValues: Partial<CityEyeFilterState>) => void;
}

export function FilterGroup({
  verticalTab,
  horizontalTab,
  solutionId,
  currentFilters,
  onFilterChange,
}: FilterGroupProps) {
  const showComparisonFilter = verticalTab === "comparison";
  const showPeopleFilters = horizontalTab === "people";
  const showTrafficFilters = horizontalTab === "traffic";

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

  const handleComparisonPeriodChange: React.Dispatch<
    React.SetStateAction<DateRange | undefined>
  > = (value) => {
    const newDate =
      typeof value === "function"
        ? value(currentFilters.comparisonPeriod)
        : value;
    onFilterChange({ comparisonPeriod: newDate });
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
        />

        {showComparisonFilter && (
          <ComparisonPeriodFilter
            currentDateRange={currentFilters.comparisonPeriod}
            onDateChange={handleComparisonPeriodChange}
            icon={<CalendarDays className="w-4 h-4 text-blue-600" />}
            iconBgColor="bg-blue-100 group-hover:bg-blue-200"
            collapsible={true}
            defaultExpanded={false}
          />
        )}

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

        <HoursFilter
          selectedHours={currentFilters.selectedHours}
          onSelectionChange={(newHours) =>
            onFilterChange({ selectedHours: newHours })
          }
          icon={<Clock className="w-4 h-4 text-blue-600" />}
          iconBgColor="bg-blue-100 group-hover:bg-blue-200"
          collapsible={true}
          defaultExpanded={false}
        />
        <DevicesFilter
          solutionId={solutionId}
          selectedDevices={currentFilters.selectedDevices}
          onSelectionChange={(newDevices) =>
            onFilterChange({ selectedDevices: newDevices })
          }
          icon={<MapPin className="w-4 h-4 text-blue-600" />}
          iconBgColor="bg-blue-100 group-hover:bg-blue-200"
          collapsible={true}
          defaultExpanded={false}
        />

        {showPeopleFilters && (
          <>
            <AgesFilter
              selectedAges={currentFilters.selectedAges}
              onSelectionChange={(newAges) =>
                onFilterChange({ selectedAges: newAges })
              }
              icon={<Users className="w-4 h-4 text-blue-600" />}
              iconBgColor="bg-blue-100 group-hover:bg-blue-200"
              collapsible={true}
              defaultExpanded={false}
            />
            <GenderFilter
              selectedGenders={currentFilters.selectedGenders}
              onSelectionChange={(newGenders) =>
                onFilterChange({ selectedGenders: newGenders })
              }
              icon={<User className="w-4 h-4 text-blue-600" />}
              iconBgColor="bg-blue-100 group-hover:bg-blue-200"
              collapsible={true}
              defaultExpanded={false}
            />
          </>
        )}

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
