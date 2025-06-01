// src/app/(main)/analytics/cityeye/_components/cards/GenericAnalyticsCard.tsx

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, AlertTriangle, Info } from "lucide-react";

interface GenericAnalyticsCardProps {
  title: string;
  isLoading: boolean;
  error: string | null;
  hasData: boolean;
  emptyMessage?: string;
  children: React.ReactNode;
  className?: string;
}

/**
 * Generic analytics card component that handles common states
 * Reduces code duplication across different analytics cards
 */
export function GenericAnalyticsCard({
  title,
  isLoading,
  error,
  hasData,
  emptyMessage = "データがありません。",
  children,
  className = "",
}: GenericAnalyticsCardProps) {
  const renderContent = () => {
    if (isLoading) {
      return (
        <div className="flex flex-col items-center justify-center h-full min-h-[200px]">
          <Loader2 className="h-8 w-8 animate-spin text-primary mb-2" />
          <p className="text-sm text-muted-foreground">データを読み込み中...</p>
        </div>
      );
    }

    if (error) {
      return (
        <div className="flex flex-col items-center justify-center h-full min-h-[200px] text-destructive">
          <AlertTriangle className="h-8 w-8 mb-2" />
          <p className="text-sm font-semibold">エラー</p>
          <p className="text-xs text-center px-2">{error}</p>
        </div>
      );
    }

    if (!hasData) {
      return (
        <div className="flex flex-col items-center justify-center h-full min-h-[200px]">
          <Info className="h-8 w-8 text-muted-foreground mb-2" />
          <p className="text-sm text-muted-foreground">{emptyMessage}</p>
        </div>
      );
    }

    return children;
  };

  return (
    <Card
      className={`shadow-lg hover:shadow-xl transition-shadow rounded-none duration-300 flex flex-col ${className}`}
    >
      <CardHeader className="pb-2 pt-3 px-4">
        <CardTitle className="text-base font-semibold text-gray-700">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-grow p-3">{renderContent()}</CardContent>
    </Card>
  );
}
