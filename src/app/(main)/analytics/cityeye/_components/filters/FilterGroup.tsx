"use client";

import React from "react";
import { AnalysisPeriodFilter } from "./AnalysisPeriodFilter";
import { ComparisonPeriodFilter } from "./ComparisonPeriodFilter";
import { DaysFilter } from "./DaysFilter";
import { HoursFilter } from "./HoursFilter";
import { DevicesFilter } from "./DevicesFilter";
import { AgesFilter } from "./AgesFilter";
import { GenderFilter } from "./GenderFilter";
import { TrafficFilter } from "./TrafficFilter";
import { ScrollArea } from "@/components/ui/scroll-area";
import { CityEyeFilterState } from "@/types/cityeye/cityEyeAnalytics"; // Import the centralized filter state type
import { DateRange } from "react-day-picker";

interface FilterGroupProps {
  verticalTab: string;
  horizontalTab: string;
  solutionId: string;
  currentFilters: CityEyeFilterState;
  onFilterChange: (newFilterValues: Partial<CityEyeFilterState>) => void;
  // customerId is part of currentFilters if needed by a sub-component,
  // but DevicesFilter now uses solutionId primarily.
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
    // If value is a function, it's a functional update. Apply it to the current state.
    // Otherwise, it's a direct new value.
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

  return (
    <ScrollArea className="h-full py-4 pr-2">
      <div className="space-y-3">
        <AnalysisPeriodFilter
          currentDateRange={currentFilters.analysisPeriod}
          onDateChange={handleAnalysisPeriodChange}
        />
        {showComparisonFilter && (
          <ComparisonPeriodFilter
            currentDateRange={currentFilters.comparisonPeriod}
            onDateChange={handleComparisonPeriodChange}
            // You might want to disable comparison if analysis period is not set
            disabled={
              !currentFilters.analysisPeriod?.from ||
              !currentFilters.analysisPeriod?.to
            }
          />
        )}
        <DaysFilter
          selectedDays={currentFilters.selectedDays}
          onSelectionChange={(newDays) =>
            onFilterChange({ selectedDays: newDays })
          }
        />
        <HoursFilter
          selectedHours={currentFilters.selectedHours}
          onSelectionChange={(newHours) =>
            onFilterChange({ selectedHours: newHours })
          }
        />
        <DevicesFilter
          solutionId={solutionId} // Pass solutionId directly
          selectedDevices={currentFilters.selectedDevices}
          onSelectionChange={(newDevices) =>
            onFilterChange({ selectedDevices: newDevices })
          }
        />
        {showPeopleFilters && (
          <>
            <AgesFilter
              selectedAges={currentFilters.selectedAges}
              onSelectionChange={(newAges) =>
                onFilterChange({ selectedAges: newAges })
              }
            />
            <GenderFilter
              selectedGenders={currentFilters.selectedGenders}
              onSelectionChange={(newGenders) =>
                onFilterChange({ selectedGenders: newGenders })
              }
            />
          </>
        )}
        {showTrafficFilters && (
          <TrafficFilter
            selectedTrafficTypes={currentFilters.selectedTrafficTypes}
            onSelectionChange={(newTrafficTypes) =>
              onFilterChange({ selectedTrafficTypes: newTrafficTypes })
            }
          />
        )}
      </div>
    </ScrollArea>
  );
}
