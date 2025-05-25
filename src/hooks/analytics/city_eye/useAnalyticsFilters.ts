import { useState, useCallback } from "react";
import {
  CityEyeFilterState,
  FrontendAnalyticsFilters,
} from "@/types/cityEyeAnalytics";
import { DateRange } from "react-day-picker"; // Added for explicit type
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
  selectedTrafficTypes: ["Large", "Car", "Bike", "Bicycle"], // Assuming these match backend IDs if traffic implemented
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
      horizontalTab: string,
      periodType: "analysisPeriod" | "comparisonPeriod" // Added to specify which period
    ): FrontendAnalyticsFilters | null => {
      const datePeriodToUse: DateRange | undefined = currentFilters[periodType];

      if (!datePeriodToUse?.from || !datePeriodToUse?.to) {
        // This validation might be better handled in CityEyeClient before calling this
        // For now, let it pass if date is missing, CityEyeClient can toast
        // toast.error(`${periodType === "analysisPeriod" ? "分析" : "比較"}期間を選択してください。`);
        // return null;
      }
      if (
        currentFilters.selectedDevices.length === 0 &&
        (horizontalTab === "people" || horizontalTab === "traffic")
      ) {
        toast.error("分析対象のデバイスを1つ以上選択してください。");
        return null;
      }

      // Ensure dates are properly formatted even if only one part of the range is initially set
      const startTime = datePeriodToUse?.from
        ? formatISO(startOfDay(datePeriodToUse.from))
        : undefined;
      const endTime = datePeriodToUse?.to
        ? formatISO(endOfDay(datePeriodToUse.to))
        : undefined;

      if (!startTime || !endTime) {
        // Let CityEyeClient handle this toast if period is mandatory for the call
        return null;
      }

      return {
        device_ids: currentFilters.selectedDevices,
        start_time: startTime,
        end_time: endTime,
        days: currentFilters.selectedDays,
        hours: currentFilters.selectedHours,
        genders:
          horizontalTab === "people"
            ? currentFilters.selectedGenders
            : undefined,
        age_groups:
          horizontalTab === "people" ? currentFilters.selectedAges : undefined,
        // polygon_ids_in and polygon_ids_out will be needed for traffic tab
      };
    },
    []
  );

  return {
    filters,
    setFilters,
    activeApiFilters, // This will now primarily be for the "main" analysis data
    setActiveApiFilters,
    handleFilterChange,
    validateAndPrepareApiFilters,
  };
}
