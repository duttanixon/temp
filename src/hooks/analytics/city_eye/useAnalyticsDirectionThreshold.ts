import { useState, useCallback, useEffect } from "react";
import { FrontendCityEyeAnalyticsPerDeviceDirectionResponse } from "@/types/cityeye/cityEyeAnalytics";
import { analyticsDirectionService } from "@/services/cityeye/cityEyeAnalyticsDirectionService";
import { toast } from "sonner";

interface UseAnalyticsDirectionThresholdProps {
  solutionId: string; // Solution ID for filtering
  customerId: string; // Customer ID for filtering
}

export function useAnalyticsDirectionThreshold({
  solutionId,
  customerId,
}: UseAnalyticsDirectionThresholdProps) {
  const [rawData, setRawData] =
    useState<FrontendCityEyeAnalyticsPerDeviceDirectionResponse | null>(null);

  const [isLoading, setIsLoading] = useState(false);

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
  const fetchData = useCallback(async () => {
    if (
      !customerId ||
      customerId === "N/A" ||
      !solutionId ||
      solutionId === "N/A"
    ) {
      setError("顧客・ソリューションIDが無効です");
      return;
    }

    setIsLoading(true);
    setError(null);
    setRawData(null);

    try {
      const response =
        await analyticsDirectionService.getHumanFlowAnalyticsDirection({
          customer_id: customerId,
          solution_id: solutionId,
        });

      // --- Success ---
      setRawData(response);
      console.log("Analytics Direction Threshold Data:", response);

      if (Object.keys(solutionId).length > 0) {
        toast.success("閾値データ取得完了");
      }
    } catch (err) {
      // --- Error Handling ---
      const errorMessage =
        err instanceof Error ? err.message : "閾値データの取得に失敗しました";

      setError(errorMessage);
      toast.error("閾値データ取得エラー", {
        description: errorMessage,
      });
    } finally {
      // --- Request End ---
      setIsLoading(false);
    }
  }, [solutionId, customerId]);

  useEffect(() => {
    if (solutionId && customerId) {
      fetchData();
    }
  }, [fetchData, solutionId, customerId]);

  return {
    rawData,
    isLoading,
    error,
    fetchData,
  };
}
