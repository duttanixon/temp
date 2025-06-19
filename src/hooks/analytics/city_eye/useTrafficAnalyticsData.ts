/**
 * CityEye Traffic Analytics Data Fetching Hook
 *
 * This hook manages the traffic analytics data fetching lifecycle including:
 * - API calls to traffic analytics service
 * - Loading state management
 * - Error handling with user feedback
 * - Smart fetching based on filter and query parameter changes
 */

import { useState, useEffect, useCallback } from "react";
import {
  FrontendTrafficAnalyticsFilters,
  FrontendCityEyeTrafficAnalyticsPerDeviceResponse,
} from "@/types/cityeye/cityEyeAnalytics";
import { analyticsService } from "@/services/cityeye/cityEyeAnalyticsService";
import { toast } from "sonner";

// ============================================================================
// HOOK INTERFACE
// ============================================================================

interface UseTrafficAnalyticsDataProps {
  /** Validated API filters from useAnalyticsFilters */
  activeApiFilters: FrontendTrafficAnalyticsFilters | null;

  /** Dynamic query parameters specifying which analytics to fetch */
  queryParams?: Record<string, boolean>;
}

// ============================================================================
// MAIN HOOK
// ============================================================================

export function useTrafficAnalyticsData({
  activeApiFilters,
  queryParams = {},
}: UseTrafficAnalyticsDataProps) {
  // ============================================================================
  // STATE MANAGEMENT
  // ============================================================================

  /** Raw traffic analytics data from API */
  const [rawData, setRawData] =
    useState<FrontendCityEyeTrafficAnalyticsPerDeviceResponse | null>(null);

  /** Loading state for UI spinners */
  const [isLoading, setIsLoading] = useState(false);

  /** Error state with user-friendly messages */
  const [error, setError] = useState<string | null>(null);

  // ============================================================================
  // DATA FETCHING LOGIC
  // ============================================================================

  /**
   * Fetches traffic analytics data from the API
   */
  const fetchData = useCallback(
    async (filtersToUse: FrontendTrafficAnalyticsFilters) => {
      // --- Request Start ---
      setIsLoading(true);
      setError(null);
      setRawData(null);

      try {
        // --- API Call ---
        const response = await analyticsService.getTrafficFlowAnalytics(
          filtersToUse,
          queryParams
        );

        // --- Success ---
        setRawData(response);

        // Only show success toast if actual data was requested
        if (Object.keys(queryParams).length > 0) {
          toast.success("交通量データ取得完了");
        }
      } catch (err) {
        // --- Error Handling ---
        const errorMessage =
          err instanceof Error ? err.message : "交通量データの取得に失敗しました";

        setError(errorMessage);
        toast.error("交通量データ取得エラー", {
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
    /** Raw traffic analytics data from API (null if no data) */
    rawData,

    /** Loading state for UI feedback */
    isLoading,

    /** Error message if request failed */
    error,

    /** Manual fetch function (typically not needed due to automatic fetching) */
    fetchData,
  };
}