"use client";

import { useState } from "react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";
import AnalyticsCard from "./AnalyticsCard";

export default function CityEyeClient() {
  const [verticalTab, setVerticalTab] = useState("分析表示");
  const [horizontalTab, setHorizontalTab] = useState("分析(人流)");

  // Titles for the six cards
  const cardTitles = [
    "カメラマップ",
    "総人数",
    "属性別分析",
    "時系列分析",
    "人流構成",
    "期間内イベント一覧",
  ];

  return (
    <div className="flex flex-col md:flex-row h-full gap-4">
      {/*tabs on left side */}
      <div className="w-full md:w-64 border-b md:border-b-0 md:border-r bg-[#F8F9FA]">
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
              value="comparision"
              className={cn(
                "flex-1 md:justify-start rounded text-sm py-3 px-4",
                "data-[state=active]:bg-[#3498DB] data-[state=active]:text-white"
              )}
            >
              比較表示
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

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
              value="daily"
              className="text-xs md:text-sm py-2 px-3 data-[state=active]:bg-[#3498DB] data-[state=active]:text-white"
            >
              人流
            </TabsTrigger>
            <TabsTrigger
              value="weekly"
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
        {/* Content based on the selected vertical tab */}
        {verticalTab === "overview" && (
          <div className="grid grid-cols-1 py-20 md:grid-cols-2 gap-x-1 gap-y-2 md:py-6">
            {cardTitles.map((title, index) => (
              <AnalyticsCard key={index} title={title} />
            ))}
          </div>
        )}

        {verticalTab === "comparison" && (
          <div className="p-6 bg-white rounded-lg shadow-md">
            <h2 className="text-xl font-semibold mb-4">比較表示エリア</h2>
            <p className="text-gray-600">
              ここに比較表示のためのコンテンツが表示されます。
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
