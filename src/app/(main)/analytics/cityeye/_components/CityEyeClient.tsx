"use client";

import { useState } from "react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";
import AnalyticsCard from "./AnalyticsCard";
import { FilterGroup } from "./filters/FilterGroup";

interface CityEyeClientProps {
  solutionId: string;
}
export default function CityEyeClient({ solutionId }: CityEyeClientProps) {
  const [verticalTab, setVerticalTab] = useState("overview");
  const [horizontalTab, setHorizontalTab] = useState("people");

  // Titles for the six cards
  const cardTitles = [
    "カメラマップ",
    "総人数",
    "属性別分析",
    "時系列分析",
    "人流構成",
    "期間内イベント一覧",
  ];

  // Determine if vertical tabs should be visible
  const showVerticalTabsAndFilters =
    horizontalTab === "people" || horizontalTab === "traffic";

  // Placeholder for customerId and solutionId, replace with actual values if available
  const customerId = "your-customer-id"; // Example: replace with actual customerId

  return (
    <div className="flex flex-col md:flex-row h-full gap-4">
      {/*tabs on left side - Conditionally rendered */}
      {showVerticalTabsAndFilters && (
        <div className="w-full md:w-90 border-b md:border-b-0 md:border-r bg-[#F8F9FA] flex flex-col">
          {" "}
          {/* Increased width for filters */}
          <Tabs
            value={verticalTab}
            onValueChange={setVerticalTab}
            className="w-full"
          >
            <TabsList className="h-auto grid grid-cols-2 gap-1 rounded-none bg-transparent w-full p-0">
              <TabsTrigger
                value="overview"
                className={cn(
                  "flex-1 md:justify-start rounded text-sm py-3 px-4",
                  "data-[state=active]:bg-[#3498DB] data-[state=active]:text-white"
                )}
              >
                分析表示
              </TabsTrigger>
              <TabsTrigger
                value="comparison"
                className={cn(
                  "flex-1 md:justify-start rounded text-sm py-3 px-4",
                  "data-[state=active]:bg-[#3498DB] data-[state=active]:text-white"
                )}
              >
                比較表示
              </TabsTrigger>
            </TabsList>
          </Tabs>
          {/* Filter Group */}
          <div className="flex-grow overflow-y-auto px-2">
            {" "}
            {/* Added px-2 for padding around filters */}
            <FilterGroup
              verticalTab={verticalTab}
              horizontalTab={horizontalTab}
              customerId={customerId}
              solutionId={solutionId}
            />
          </div>
        </div>
      )}

      {/* Main content area */}
      <div className="flex-1">
        {/* Second tab group - horizontal tabs in center */}
        <Tabs
          value={horizontalTab}
          onValueChange={setHorizontalTab}
          className="w-full"
        >
          <TabsList className="w-full grid grid-cols-2 md:grid-cols-4 gap-1">
            <TabsTrigger
              value="people"
              className="text-xs md:text-sm py-2 px-3 data-[state=active]:bg-[#3498DB] data-[state=active]:text-white"
            >
              人流
            </TabsTrigger>
            <TabsTrigger
              value="traffic"
              className="text-xs md:text-sm py-2 px-3 data-[state=active]:bg-[#3498DB] data-[state=active]:text-white"
            >
              交通量
            </TabsTrigger>
            <TabsTrigger
              value="monthly"
              className="text-xs md:text-sm py-2 px-3 data-[state=active]:bg-[#3498DB] data-[state=active]:text-white"
            >
              人流(方向)
            </TabsTrigger>
            <TabsTrigger
              value="quarterly"
              className="text-xs md:text-sm py-2 px-3 data-[state=active]:bg-[#3498DB] data-[state=active]:text-white"
            >
              交通量(方向)
            </TabsTrigger>
          </TabsList>
        </Tabs>

        {/* Content based on the selected horizontal and vertical tabs */}
        {showVerticalTabsAndFilters ? (
          <>
            {verticalTab === "overview" && (
              // <div className="grid grid-cols-1 py-20 md:grid-cols-2 gap-x-1 gap-y-2 md:py-6">
              <div className="grid grid-cols-1 py-4 md:grid-cols-2 gap-x-1 gap-y-2">
                {" "}
                {/* Reduced py */}
                {cardTitles.map((title, index) => (
                  <AnalyticsCard key={index} title={title} />
                ))}
              </div>
            )}

            {verticalTab === "comparison" && ( // Changed to "comparison"
              <div className="p-4 bg-slate-50 rounded-lg shadow-xl mt-4">
                {" "}
                {/* Reduced padding/margin */}
                {/* <div className="p-6 bg-slate-40 rounded-lg shadow-md mt-8"> */}
                <h2 className="text-xl font-semibold mb-4 text-center">
                  比較表示エリア
                </h2>
                <div className="flex flex-col md:flex-row gap-4 shadow-2xl">
                  {/* Column 1 */}
                  <div className="flex-1 space-y-2 bg-white p-4 rounded-md">
                    {" "}
                    {/* White background for column 1 cards */}
                    <div className="text-center font-semibold mb-2">
                      データセット1 (例: 昨日)
                    </div>
                    {cardTitles.map((title, index) => (
                      <AnalyticsCard
                        key={`comparison-col1-${index}`}
                        title={title}
                      />
                    ))}
                  </div>
                  {/* Column 2 */}
                  <div className="flex-1 space-y-2 bg-white p-4 rounded-md">
                    {" "}
                    {/* White background for column 2 cards */}
                    <div className="text-center font-semibold mb-2">
                      データセット2 (例: 今日)
                    </div>
                    {cardTitles.map((title, index) => (
                      <AnalyticsCard
                        key={`comparison-col2-${index}`}
                        title={title}
                      />
                    ))}
                  </div>
                </div>
              </div>
            )}
          </>
        ) : (
          // Content for when vertical tabs are hidden (monthly/quarterly horizontal tabs are active)
          <div className="p-6 mt-8 flex items-center justify-center h-[calc(100%-var(--tabs-list-height,40px))]">
            {" "}
            {/* Adjust height if needed */}
            <p className="text-gray-500 text-lg">no data available</p>
          </div>
        )}
      </div>
    </div>
  );
}
