import { analyticsDirectionService } from "@/services/cityeye/cityEyeAnalyticsDirectionService";
import {
  FrontendAnalyticsDirectionFilters,
  FrontendCityEyeAnalyticsPerDeviceDirectionResponse,
} from "@/types/cityeye/cityEyeAnalytics";
import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";

interface UseAnalyticsDirectionDataProps {
  /** Validated API filters from useAnalyticsFilters */
  activeApiFilters: FrontendAnalyticsDirectionFilters | null;
}

// ============================================================================
// MAIN HOOK
// ============================================================================

export function useHumanAnalyticsDirectionData({
  activeApiFilters,
}: UseAnalyticsDirectionDataProps) {
  // ============================================================================
  // STATE MANAGEMENT
  // ============================================================================

  /** Raw analytics data from API */
  const [rawData, setRawData] =
    useState<FrontendCityEyeAnalyticsPerDeviceDirectionResponse | null>(null);

  /** Loading state for UI spinners */
  const [isLoading, setIsLoading] = useState(false);

  /** Error state with user-friendly messages */
  const [error, setError] = useState<string | null>(null);

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
    async (filtersToUse: FrontendAnalyticsDirectionFilters) => {
      // --- Request Start ---
      setIsLoading(true);
      setError(null);
      setRawData(null);
      console.log(
        "人流分析マップデータ取得開始",
        filtersToUse,
        "activeApiFilters:",
        activeApiFilters
      );

      try {
        // --- API Call ---
        const response =
          await analyticsDirectionService.getHumanFlowAnalyticsDirection(
            filtersToUse
          );

        // --- Success ---
        setRawData(response);
        console.log("人流分析マップデータ取得成功", response);

        // Only show success toast if actual data was requested
        toast.success("人流分析マップデータ取得完了");
      } catch (err) {
        // --- Error Handling ---
        const errorMessage =
          err instanceof Error
            ? err.message
            : "人流分析マップデータの取得に失敗しました";

        setError(errorMessage);
        toast.error("人流分析マップデータ取得エラー", {
          description: errorMessage,
        });
      } finally {
        // --- Request End ---
        setIsLoading(false);
      }
    },
    [activeApiFilters]
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

    if (hasValidFilters) {
      // Conditions met - fetch data
      fetchData(activeApiFilters);
    } else {
      // Conditions not met - clear state
      setRawData(null);
      setError(null);
      setIsLoading(false);
    }
  }, [activeApiFilters, fetchData]);

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
