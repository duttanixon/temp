import { useState, useEffect, useCallback } from "react";
import {
  FrontendAnalyticsFilters,
  FrontendCityEyeAnalyticsPerDeviceResponse,
} from "@/types/cityEyeAnalytics";
import { analyticsService } from "@/services/cityEyeAnalyticsService";
import { toast } from "sonner";

interface UseAnalyticsDataProps {
  activeApiFilters: FrontendAnalyticsFilters | null;
  // horizontalTab: string; // To potentially adjust queryParams based on tab
}

export function useAnalyticsData({ activeApiFilters }: UseAnalyticsDataProps) {
  const [rawData, setRawData] =
    useState<FrontendCityEyeAnalyticsPerDeviceResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(
    async (filtersToUse: FrontendAnalyticsFilters) => {
      setIsLoading(true);
      setError(null);
      setRawData(null);

      try {
        // TODO: Adjust queryParams based on horizontalTab if different data points are needed per tab
        const queryParams = { include_total_count: true };
        const response = await analyticsService.getHumanFlowAnalytics(
          filtersToUse,
          queryParams
        );
        setRawData(response);
        toast.success("分析データ取得完了");
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "分析データの取得に失敗しました";
        setError(errorMessage);
        toast.error("分析データ取得エラー", { description: errorMessage });
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  useEffect(() => {
    if (activeApiFilters) {
      fetchData(activeApiFilters);
    } else {
      // If activeApiFilters is null, it means filters changed but not applied yet, or initial state
      setRawData(null);
      setError(null);
      setIsLoading(false);
    }
  }, [activeApiFilters, fetchData]);

  return {
    rawData,
    isLoading,
    error,
    fetchData, // Expose if manual refetch with same filters is needed
  };
}
