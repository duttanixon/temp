import { useState, useCallback } from "react";
import {
  CityEyeFilterState,
  FrontendAnalyticsFilters,
} from "@/types/cityEyeAnalytics";
import { format, startOfDay, endOfDay, subDays } from "date-fns";

// Default filter state with sensible defaults
const createDefaultFilters = (): CityEyeFilterState => ({
  analysisPeriod: {
    from: startOfDay(subDays(new Date(), 6)),
    to: endOfDay(new Date()),
  },
  comparisonPeriod: {
    from: startOfDay(subDays(new Date(), 13)),
    to: endOfDay(subDays(new Date(), 7)),
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
});

/**
 * hook for managing analytics filters
 */
export function useAnalyticsFilters() {
  const [filters, setFilters] = useState<CityEyeFilterState>(
    createDefaultFilters()
  );

  /**
   * Update filters with partial values
   * Simplified to just update state without additional side effects
   */
  const handleFilterChange = useCallback(
    (updates: Partial<CityEyeFilterState>) => {
      setFilters((prev) => ({ ...prev, ...updates }));
    },
    []
  );

  /**
   * Validate and prepare filters for API
   * Consolidated validation logic into single function
   */
  const validateAndPrepareApiFilters = useCallback(
    (
      currentFilters: CityEyeFilterState,
      horizontalTab: string,
      periodType: "analysisPeriod" | "comparisonPeriod"
    ): FrontendAnalyticsFilters | null => {
      const period = currentFilters[periodType];

      // Basic validation
      if (!period?.from || !period?.to) {
        return null;
      }

      if (currentFilters.selectedDevices.length === 0) {
        return null;
      }

      // Format dates
      const startTime = format(
        startOfDay(period.from),
        "yyyy-MM-dd'T'HH:mm:ss"
      );
      const endTime = format(endOfDay(period.to), "yyyy-MM-dd'T'HH:mm:ss");

      // Build API filters object
      return {
        device_ids: currentFilters.selectedDevices,
        start_time: startTime,
        end_time: endTime,
        days: currentFilters.selectedDays,
        hours: currentFilters.selectedHours,
        // Include demographic filters only for people analytics
        ...(horizontalTab === "people" && {
          genders: currentFilters.selectedGenders,
          age_groups: currentFilters.selectedAges,
        }),
      };
    },
    []
  );

  /**
   * Reset filters to defaults
   * Utility function for clearing all filters
   */
  const resetFilters = useCallback(() => {
    setFilters(createDefaultFilters());
  }, []);

  return {
    filters,
    handleFilterChange,
    validateAndPrepareApiFilters,
    resetFilters,
  };
}
