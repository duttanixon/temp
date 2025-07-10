import { useState, useCallback, useEffect } from "react";
import { FrontendCityEyeAnalyticsPerDeviceDirectionThresholdsResponse } from "@/types/cityeye/cityEyeAnalytics";
import { analyticsDirectionService } from "@/services/cityeye/cityEyeAnalyticsDirectionService";
import { toast } from "sonner";

interface UseAnalyticsDirectionPutThresholdProps {
  customer_id?: string;
  solution_id?: string;
  thresholds?: {
    traffic_count_thresholds?: number[];
    human_count_thresholds?: number[];
  };
}

export function useAnalyticsDirectionPutThreshold({
  solution_id: solutionId,
  customer_id: customerId,
  thresholds = {
    traffic_count_thresholds: [],
    human_count_thresholds: [],
  },
}: UseAnalyticsDirectionPutThresholdProps) {
  const [rawData, setRawData] =
    useState<FrontendCityEyeAnalyticsPerDeviceDirectionThresholdsResponse | null>(
      null
    );

  const [isLoading, setIsLoading] = useState(false);

  const [error, setError] = useState<string | null>(null);

  /**
   * Fetches analytics data from the API
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
        await analyticsDirectionService.putFlowAnalyticsDirectionThreshold({
          customer_id: customerId,
          solution_id: solutionId,
          thresholds,
        });

      // --- Success ---
      setRawData(response);
      console.log("Analytics Direction Threshold Data:", response);

      if (Object.keys(solutionId).length > 0) {
        toast.success("閾値データ更新完了");
      }
    } catch (err) {
      // --- Error Handling ---
      const errorMessage =
        err instanceof Error ? err.message : "閾値データの更新に失敗しました";

      setError(errorMessage);
      toast.error("閾値データ更新エラー", {
        description: errorMessage,
      });
    } finally {
      // --- Request End ---
      setIsLoading(false);
    }
  }, [solutionId, customerId, thresholds]);

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
