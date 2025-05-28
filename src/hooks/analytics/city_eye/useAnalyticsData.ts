import { useState, useEffect, useCallback } from "react";
import {
  FrontendAnalyticsFilters,
  FrontendCityEyeAnalyticsPerDeviceResponse,
} from "@/types/cityEyeAnalytics";
import { analyticsService } from "@/services/cityEyeAnalyticsService";
import { toast } from "sonner";

interface UseAnalyticsDataProps {
  activeApiFilters: FrontendAnalyticsFilters | null;
  queryParams?: Record<string, boolean>; // Make queryParams dynamic
}

export function useAnalyticsData({
  activeApiFilters,
  queryParams = {},
}: UseAnalyticsDataProps) {
  // Added queryParams
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
        // Use the passed queryParams
        const response = await analyticsService.getHumanFlowAnalytics(
          filtersToUse,
          queryParams // Use dynamic queryParams
        );
        setRawData(response);
        if (Object.keys(queryParams).length > 0) {
          // Only toast if actual data was requested
          toast.success("分析データ取得完了");
        }
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "分析データの取得に失敗しました";
        setError(errorMessage);
        toast.error("分析データ取得エラー", { description: errorMessage });
      } finally {
        setIsLoading(false);
      }
    },
    [queryParams] // Add queryParams to dependency array
  );

  useEffect(() => {
    if (activeApiFilters && Object.keys(queryParams).length > 0) {
      // Also check if queryParams are meaningful
      fetchData(activeApiFilters);
    } else {
      setRawData(null);
      setError(null);
      setIsLoading(false);
    }
  }, [activeApiFilters, fetchData, queryParams]);

  return {
    rawData,
    isLoading,
    error,
    fetchData,
  };
}
