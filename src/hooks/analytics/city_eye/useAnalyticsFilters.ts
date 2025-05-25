import { useState, useCallback } from "react";
import {
  CityEyeFilterState,
  FrontendAnalyticsFilters,
} from "@/types/cityEyeAnalytics";
import { formatISO, startOfDay, endOfDay, subDays } from "date-fns";
import { toast } from "sonner";

const initialAnalysisDateFrom = startOfDay(subDays(new Date(), 6));
const initialAnalysisDateTo = endOfDay(new Date());

export const initialFilterStateValues: CityEyeFilterState = {
  analysisPeriod: { from: initialAnalysisDateFrom, to: initialAnalysisDateTo },
  comparisonPeriod: {
    from: startOfDay(subDays(initialAnalysisDateFrom, 7)),
    to: endOfDay(subDays(initialAnalysisDateTo, 7)),
  },
  selectedDays: [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
  ],
  selectedHours: Array.from(
    { length: 24 },
    (_, i) => `${String(i).padStart(2, "0")}:00`
  ),
  selectedDevices: [],
  selectedAges: ["under_18", "18_to_29", "30_to_49", "50_to_64", "over_64"],
  selectedGenders: ["male", "female"],
  selectedTrafficTypes: ["Large", "Car", "Bike", "Bicycle"],
};

export function useAnalyticsFilters(
  initialState: CityEyeFilterState = initialFilterStateValues
) {
  const [filters, setFilters] = useState<CityEyeFilterState>(initialState);
  const [activeApiFilters, setActiveApiFilters] =
    useState<FrontendAnalyticsFilters | null>(null);

  const handleFilterChange = useCallback(
    (newFilterValues: Partial<CityEyeFilterState>) => {
      setFilters((prevFilters) => ({
        ...prevFilters,
        ...newFilterValues,
      }));
      setActiveApiFilters(null); // Reset active filters, data becomes stale until applied
    },
    []
  );

  const validateAndPrepareApiFilters = useCallback(
    (
      currentFilters: CityEyeFilterState,
      horizontalTab: string
    ): FrontendAnalyticsFilters | null => {
      if (
        !currentFilters.analysisPeriod?.from ||
        !currentFilters.analysisPeriod?.to
      ) {
        toast.error("分析期間を選択してください。");
        return null;
      }
      if (
        currentFilters.selectedDevices.length === 0 &&
        (horizontalTab === "people" || horizontalTab === "traffic")
      ) {
        toast.error("分析対象のデバイスを1つ以上選択してください。");
        return null;
      }

      return {
        device_ids: currentFilters.selectedDevices,
        start_time: formatISO(startOfDay(currentFilters.analysisPeriod.from)),
        end_time: formatISO(endOfDay(currentFilters.analysisPeriod.to)),
        days: currentFilters.selectedDays,
        hours: currentFilters.selectedHours,
        genders:
          horizontalTab === "people"
            ? currentFilters.selectedGenders
            : undefined,
        age_groups:
          horizontalTab === "people" ? currentFilters.selectedAges : undefined,
        // Add polygon_ids_in and polygon_ids_out if/when traffic tab is implemented
        // polygon_ids_in: horizontalTab === "traffic" ? currentFilters.selectedPolygonsIn : undefined,
        // polygon_ids_out: horizontalTab === "traffic" ? currentFilters.selectedPolygonsOut : undefined,
      };
    },
    []
  );

  return {
    filters,
    setFilters, // Expose setFilters if direct manipulation is needed, e.g., for resetting
    activeApiFilters,
    setActiveApiFilters,
    handleFilterChange,
    validateAndPrepareApiFilters,
  };
}
