"use client";

import React from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Loader2, AlertTriangle, Info } from "lucide-react";
import ButterflyChart from "@/components/charts/butterfly-chart"; // Adjusted path
import { ProcessedAgeGenderDistributionData } from "@/types/cityeye/cityEyeAnalytics";

interface AgeGenderButterflyChartCardProps {
  title: string;
  description?: string;
  data: ProcessedAgeGenderDistributionData | null;
  isLoading: boolean;
  error: string | null;
  hasAttemptedFetch: boolean;
  chartHeight?: number; // Optional override
  barSize?: number; // Optional override
}

export default function AgeGenderButterflyChartCard({
  title,
  description,
  data,
  isLoading,
  error,
  hasAttemptedFetch,
  chartHeight, // Use this if provided, otherwise ButterflyChart default
  barSize, // Use this if provided, otherwise ButterflyChart default
}: AgeGenderButterflyChartCardProps) {
  const renderContent = () => {
    if (isLoading) {
      return (
        <div className="flex flex-col items-center justify-center h-full min-h-[250px]">
          <Loader2 className="h-8 w-8 animate-spin text-primary mb-2" />
          <p className="text-sm text-muted-foreground">データを読み込み中...</p>
        </div>
      );
    }

    if (error && hasAttemptedFetch) {
      return (
        <div className="flex flex-col items-center justify-center h-full min-h-[250px] text-destructive">
          <AlertTriangle className="h-8 w-8 mb-2" />
          <p className="text-sm font-semibold">エラー</p>
          <p className="text-xs text-center px-2">{error}</p>
        </div>
      );
    }

    if (data?.error && hasAttemptedFetch) {
      // Check for processing error from util
      return (
        <div className="flex flex-col items-center justify-center h-full min-h-[250px] text-destructive">
          <AlertTriangle className="h-8 w-8 mb-2" />
          <p className="text-sm font-semibold">データ処理エラー</p>
          <p className="text-xs text-center px-2">{data.error}</p>
        </div>
      );
    }

    if (!hasAttemptedFetch) {
      return (
        <div className="flex flex-col items-center justify-center h-full min-h-[250px]">
          <Info className="h-8 w-8 text-muted-foreground mb-2" />
          <p className="text-sm text-muted-foreground p-4 text-center">
            フィルターを適用して年齢性別構成データを表示します。
          </p>
        </div>
      );
    }

    if (!data || (!data.groupAData.length && !data.groupBData.length)) {
      return (
        <div className="flex flex-col items-center justify-center h-full min-h-[250px]">
          <Info className="h-8 w-8 text-muted-foreground mb-2" />
          <p className="text-sm text-muted-foreground">データがありません。</p>
          {hasAttemptedFetch && !error && (
            <p className="text-xs text-muted-foreground text-center px-2">
              選択されたフィルター条件に一致するデータが見つかりませんでした。
            </p>
          )}
        </div>
      );
    }

    return (
      <ButterflyChart
        groupALabel={data.groupALabel}
        groupBLabel={data.groupBLabel}
        groupAData={data.groupAData}
        groupBData={data.groupBData}
        unit="人" // Assuming unit is "people"
        barSize={barSize} // Pass through optional override
        // chartHeight prop is handled by the ButterflyChart itself based on categories
      />
    );
  };

  return (
    <Card className="shadow-lg hover:shadow-xl transition-shadow rounded-none duration-300 flex flex-col col-span-1 md:col-span-2 h-[560px]">
      {/* Span 2 columns */}
      <CardHeader className="pb-2 pt-3 px-4">
        <CardTitle className="text-base font-semibold text-gray-700">
          {title}
        </CardTitle>
        {description && (
          <CardDescription className="text-xs text-muted-foreground">
            {description}
          </CardDescription>
        )}
      </CardHeader>
      <CardContent className="flex-grow p-3">{renderContent()}</CardContent>
    </Card>
  );
}
