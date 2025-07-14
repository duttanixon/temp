import { useState, useCallback } from "react";
import { FrontendCityEyeAnalyticsPerDeviceDirectionThresholdsResponse } from "@/types/cityeye/cityEyeAnalytics";
import { analyticsDirectionService } from "@/services/cityeye/cityEyeAnalyticsDirectionService";
import { toast } from "sonner";

export function useAnalyticsDirectionPutThreshold() {
  const [rawData, setRawData] =
    useState<FrontendCityEyeAnalyticsPerDeviceDirectionThresholdsResponse | null>(
      null
    );
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Fetches analytics data from the API
   * @param params - request params
   */
  const fetchData = useCallback(
    async (params: {
      solution_id: string;
      customer_id: string;
      thresholds?: {
        traffic_count_thresholds?: number[];
        human_count_thresholds?: number[];
      };
    }) => {
      const { solution_id, customer_id, thresholds } = params;
      if (
        !customer_id ||
        customer_id === "N/A" ||
        !solution_id ||
        solution_id === "N/A" ||
        !thresholds
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
            customer_id,
            solution_id,
            thresholds,
          });

        // --- Success ---
        setRawData(response);
        console.log("Analytics Direction Threshold Data:", response);

        if (Object.keys(solution_id).length > 0) {
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
    },
    []
  );

  return {
    rawData,
    isLoading,
    error,
    fetchData,
  };
}
