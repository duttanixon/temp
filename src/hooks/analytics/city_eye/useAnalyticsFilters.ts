/**
 * CityEye Analytics Filter Management Hook
 *
 * This hook manages the analytics filter state and provides utilities for
 * converting UI filter state to API-ready format with validation.
 *
 * Key Features:
 * - Two-stage filter system (UI filters vs applied API filters)
 * - Smart validation before API calls
 * - Date range handling with proper formatting
 * - Tab-aware filter preparation (people vs traffic analytics)
 *
 * Usage Pattern:
 * 1. User modifies filters → UI state updates instantly
 * 2. User applies filters → Validation → API format conversion
 * 3. Valid filters trigger data fetching in useAnalyticsData
 */

import { useState, useCallback } from "react";
import {
  CityEyeFilterState,
  FrontendAnalyticsFilters,
} from "@/types/cityEyeAnalytics";
import { DateRange } from "react-day-picker";
import { format, startOfDay, endOfDay, subDays } from "date-fns";
import { toast } from "sonner";

// ============================================================================
// CONSTANTS & INITIAL STATE
// ============================================================================

/**
 * Default date ranges for immediate usability
 * Analysis: Last 7 days
 * Comparison: 7 days before analysis period
 */
const DEFAULT_ANALYSIS_START = startOfDay(subDays(new Date(), 6));
const DEFAULT_ANALYSIS_END = endOfDay(new Date());

/**
 * Complete initial filter state with sensible defaults
 * Users can start analyzing immediately after selecting devices
 */
export const initialFilterStateValues: CityEyeFilterState = {
  // Date Ranges
  analysisPeriod: {
    from: DEFAULT_ANALYSIS_START,
    to: DEFAULT_ANALYSIS_END,
  },
  comparisonPeriod: {
    from: startOfDay(subDays(DEFAULT_ANALYSIS_START, 7)),
    to: endOfDay(subDays(DEFAULT_ANALYSIS_END, 7)),
  },

  // Time Filters (all inclusive by default)
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

  // Device Selection (requires user input)
  selectedDevices: [],

  // Demographics (all inclusive by default)
  selectedAges: ["under_18", "18_to_29", "30_to_49", "50_to_64", "over_64"],
  selectedGenders: ["male", "female"],

  // Traffic Types (for future traffic tab)
  selectedTrafficTypes: ["Large", "Car", "Bike", "Bicycle"],
};

// ============================================================================
// MAIN HOOK
// ============================================================================

export function useAnalyticsFilters(
  initialState: CityEyeFilterState = initialFilterStateValues
) {
  // ============================================================================
  // STATE MANAGEMENT
  // ============================================================================

  /** Current UI filter state - updates immediately on user interaction */
  const [filters, setFilters] = useState<CityEyeFilterState>(initialState);

  /** Applied API filters - only set when filters are validated and applied */
  const [activeApiFilters, setActiveApiFilters] =
    useState<FrontendAnalyticsFilters | null>(null);

  // ============================================================================
  // FILTER UPDATE HANDLER
  // ============================================================================

  /**
   * Updates UI filter state and resets active API filters
   *
   * This makes the current data "stale" until new filters are applied,
   * allowing users to experiment with filter combinations without
   * triggering API calls on every change.
   *
   * @param newFilterValues - Partial filter updates to merge with current state
   */
  const handleFilterChange = useCallback(
    (newFilterValues: Partial<CityEyeFilterState>) => {
      setFilters((prevFilters) => ({
        ...prevFilters,
        ...newFilterValues,
      }));

      // Reset active filters - data becomes stale until re-applied
      setActiveApiFilters(null);
    },
    []
  );

  // ============================================================================
  // VALIDATION & API PREPARATION
  // ============================================================================

  /**
   * Validates current filter state and converts to API format
   *
   * Performs comprehensive validation including:
   * - Date range completeness
   * - Device selection requirements
   * - Tab-specific filter inclusion
   *
   * @param currentFilters - Current filter state to validate
   * @param horizontalTab - Current tab context ("people" | "traffic")
   * @param periodType - Which date period to use ("analysisPeriod" | "comparisonPeriod")
   * @returns Valid API filters or null if validation fails
   */
  const validateAndPrepareApiFilters = useCallback(
    (
      currentFilters: CityEyeFilterState,
      horizontalTab: string,
      periodType: "analysisPeriod" | "comparisonPeriod"
    ): FrontendAnalyticsFilters | null => {
      // --- Date Range Validation ---
      const datePeriodToUse: DateRange | undefined = currentFilters[periodType];

      if (!datePeriodToUse?.from || !datePeriodToUse?.to) {
        // Note: Date validation is handled upstream in CityEyeClient
        // Allowing this to pass through for now
        return null;
      }

      // --- Device Selection Validation ---
      if (
        currentFilters.selectedDevices.length === 0 &&
        (horizontalTab === "people" || horizontalTab === "traffic")
      ) {
        toast.error("分析対象のデバイスを1つ以上選択してください。");
        return null;
      }

      // --- Date Formatting ---
      const startTime = format(
        startOfDay(datePeriodToUse.from),
        "yyyy-MM-dd'T'HH:mm:ss"
      );
      const endTime = format(
        endOfDay(datePeriodToUse.to),
        "yyyy-MM-dd'T'HH:mm:ss"
      );

      if (!startTime || !endTime) {
        // Let CityEyeClient handle mandatory period validation
        return null;
      }

      // --- Build API Filter Object ---
      return {
        // Core filters (always included)
        device_ids: currentFilters.selectedDevices,
        start_time: startTime,
        end_time: endTime,
        days: currentFilters.selectedDays,
        hours: currentFilters.selectedHours,

        // Tab-specific filters (only for people analytics)
        genders:
          horizontalTab === "people"
            ? currentFilters.selectedGenders
            : undefined,
        age_groups:
          horizontalTab === "people" ? currentFilters.selectedAges : undefined,

        // Future: polygon_ids_in/out for traffic tab
      };
    },
    []
  );

  // ============================================================================
  // RETURN INTERFACE
  // ============================================================================

  return {
    /** Current UI filter state */
    filters,

    /** Direct filter state setter (use handleFilterChange instead) */
    setFilters,

    /** Currently applied API filters (null if none applied) */
    activeApiFilters,

    /** Set active API filters (typically after validation) */
    setActiveApiFilters,

    /** Update UI filters without triggering API calls */
    handleFilterChange,

    /** Validate and convert filters to API format */
    validateAndPrepareApiFilters,
  };
}
