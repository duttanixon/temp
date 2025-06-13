/**
 * CityEye Analytics Data Fetching Hook
 *
 * This hook manages the analytics data fetching lifecycle including:
 * - API calls to analytics service
 * - Loading state management
 * - Error handling with user feedback
 * - Smart fetching based on filter and query parameter changes
 *
 * Key Features:
 * - Only fetches when both filters and query params are valid
 * - Automatic data clearing when filters become invalid
 * - User feedback via toast notifications
 * - Comprehensive error handling
 *
 * Usage:
 * - Typically paired with useAnalyticsFilters
 * - queryParams specify which analytics to request
 * - activeApiFilters come from validated filter state
 */

import { useState, useEffect, useCallback } from "react";
import {
  FrontendAnalyticsFilters,
  FrontendCityEyeAnalyticsPerDeviceResponse,
} from "@/types/cityEyeAnalytics";
import { analyticsService } from "@/services/cityEyeAnalyticsService";
import { toast } from "sonner";

// ============================================================================
// HOOK INTERFACE
// ============================================================================

interface UseAnalyticsDataProps {
  /** Validated API filters from useAnalyticsFilters */
  activeApiFilters: FrontendAnalyticsFilters | null;

  /** Dynamic query parameters specifying which analytics to fetch */
  queryParams?: Record<string, boolean>;
}

// ============================================================================
// MAIN HOOK
// ============================================================================

export function useHumanAnalyticsData({
  activeApiFilters,
  queryParams = {},
}: UseAnalyticsDataProps) {
  // ============================================================================
  // STATE MANAGEMENT
  // ============================================================================

  /** Raw analytics data from API */
  const [rawData, setRawData] =
    useState<FrontendCityEyeAnalyticsPerDeviceResponse | null>(null);

  /** Loading state for UI spinners */
  const [isLoading, setIsLoading] = useState(false);

  /** Error state with user-friendly messages */
  const [error, setError] = useState<string | null>(null);

  // ============================================================================
  // DATA FETCHING LOGIC
  // ============================================================================

  /**
   * Fetches analytics data from the API
   *
   * Handles the complete request lifecycle:
   * - Sets loading state
   * - Clears previous data and errors
   * - Makes API call with filters and query params
   * - Updates state based on success/failure
   * - Shows user feedback via toast notifications
   *
   * @param filtersToUse - Validated API filters for the request
   */
  const fetchData = useCallback(
    async (filtersToUse: FrontendAnalyticsFilters) => {
      // --- Request Start ---
      setIsLoading(true);
      setError(null);
      setRawData(null);

      try {
        // --- API Call ---
        const response = await analyticsService.getHumanFlowAnalytics(
          filtersToUse,
          queryParams
        );

        // --- Success ---
        setRawData(response);

        // Only show success toast if actual data was requested
        if (Object.keys(queryParams).length > 0) {
          toast.success("人流分析データ取得完了");
        }
      } catch (err) {
        // --- Error Handling ---
        const errorMessage =
          err instanceof Error
            ? err.message
            : "人流分析データの取得に失敗しました";

        setError(errorMessage);
        toast.error("人流分析データ取得エラー", {
          description: errorMessage,
        });
      } finally {
        // --- Request End ---
        setIsLoading(false);
      }
    },
    [queryParams]
  );

  // ============================================================================
  // AUTOMATIC FETCH TRIGGER
  // ============================================================================

  /**
   * Effect: Automatically fetch data when conditions are met
   *
   * Fetching Conditions:
   * 1. activeApiFilters exists (filters have been validated and applied)
   * 2. queryParams has content (specific analytics are requested)
   *
   * When conditions are not met:
   * - Clears existing data
   * - Resets error state
   * - Stops loading
   */
  useEffect(() => {
    const hasValidFilters = activeApiFilters !== null;
    const hasQueryParams = Object.keys(queryParams).length > 0;

    if (hasValidFilters && hasQueryParams) {
      // Conditions met - fetch data
      fetchData(activeApiFilters);
    } else {
      // Conditions not met - clear state
      setRawData(null);
      setError(null);
      setIsLoading(false);
    }
  }, [activeApiFilters, fetchData, queryParams]);

  // ============================================================================
  // RETURN INTERFACE
  // ============================================================================

  return {
    /** Raw analytics data from API (null if no data) */
    rawData,

    /** Loading state for UI feedback */
    isLoading,

    /** Error message if request failed */
    error,

    /** Manual fetch function (typically not needed due to automatic fetching) */
    fetchData,
  };
}
