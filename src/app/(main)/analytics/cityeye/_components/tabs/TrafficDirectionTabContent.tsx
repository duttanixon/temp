"use client";

import { useGetCustomer } from "@/app/(main)/_components/_hooks/useGetCustomer";
import { ProcessedTrafficAnalyticsData } from "@/types/cityeye/cityEyeAnalytics";
import React from "react";
import TrafficDirectionView from "@/app/(main)/analytics/cityeye/_components/views/TrafficDirectionView";

interface TrafficDirectionTabContentProps {
  mainProcessedData: ProcessedTrafficAnalyticsData | null;
  isLoadingMain: boolean;
  errorMain: string | null;
  hasAttemptedFetchMain: boolean;
}

export default function TrafficDirectionTabContent({
  mainProcessedData,
  isLoadingMain,
  errorMain,
  hasAttemptedFetchMain,
}: TrafficDirectionTabContentProps) {
  const { customer } = useGetCustomer();
  console.log("TrafficDirectionTabContent customer:", customer);
  // Placeholder implementation
  return (
    <>
      <TrafficDirectionView
        processedData={mainProcessedData}
        isLoading={isLoadingMain}
        error={errorMain}
        hasAttemptedFetch={hasAttemptedFetchMain}
      />
      {/* <div className="p-6 mt-4 flex items-center justify-center h-[calc(100%-var(--tabs-list-height,40px))] bg-white rounded-lg shadow">
        <p className="text-gray-500 text-lg">交通量(方向) 分析 - 未実装</p>
        {customer && (
          <option key={customer.id} value={customer.id}>
            {customer.name}
          </option>
        )}
      </div> */}
    </>
  );
}
