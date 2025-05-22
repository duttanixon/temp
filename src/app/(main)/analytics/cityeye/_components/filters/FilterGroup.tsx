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

interface FilterGroupProps {
  verticalTab: string;
  horizontalTab: string;
  // Add any other props needed for the filter components, e.g., customerId, solutionId
  customerId?: string;
  solutionId?: string;
}

export function FilterGroup({
  verticalTab,
  horizontalTab,
  customerId,
  solutionId,
}: FilterGroupProps) {
  const showComparisonFilter = verticalTab === "comparison";
  const showPeopleFilters = horizontalTab === "people";
  const showTrafficFilters = horizontalTab === "traffic";

  const commonFilters = (
    <>
      <AnalysisPeriodFilter />
      {showComparisonFilter && <ComparisonPeriodFilter />}
      <DaysFilter />
      <HoursFilter />
      <DevicesFilter customerId={customerId} solutionId={solutionId} />
    </>
  );
  return (
    <ScrollArea className="h-full py-4 pr-2">
      {" "}
      {/* Added pr-2 for scrollbar spacing */}
      <div className="space-y-3">
        {" "}
        {/* Increased spacing between filters */}
        {commonFilters}
        {showPeopleFilters && (
          <>
            <AgesFilter />
            <GenderFilter />
          </>
        )}
        {showTrafficFilters && <TrafficFilter />}
      </div>
    </ScrollArea>
  );
}
