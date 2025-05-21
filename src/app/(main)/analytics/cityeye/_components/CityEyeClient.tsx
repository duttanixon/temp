"use client";

import { useState } from "react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";

export default function CityEyeClient() {
  const [verticalTab, setVerticalTab] = useState("分析表示");
  const [horizontalTab, setHorizontalTab] = useState("分析(人流)");
  return (
    <div className="flex flex-col md:flex-row h-full gap-8">
      {/* First tab group - vertical tabs on left side */}
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
              value="details"
              className={cn(
                "flex-1 md:justify-start rounded text-sm py-3 px-4",
                "data-[state=active]:bg-[#3498DB] data-[state=active]:text-white"
              )}
            >
              比較表示
            </TabsTrigger>
          </TabsList>

          {/* Empty TabsContent components (required by the Tabs component) */}
          <TabsContent value="overview" className="sr-only"></TabsContent>
          <TabsContent value="details" className="sr-only"></TabsContent>
        </Tabs>
      </div>

      {/* Main content area */}
      <div className="flex-1">
        <div className="max-w-5xl mx-auto">
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

            {/* Empty TabsContent components (required by the Tabs component) */}
            <TabsContent value="daily" className="sr-only"></TabsContent>
            <TabsContent value="weekly" className="sr-only"></TabsContent>
            <TabsContent value="monthly" className="sr-only"></TabsContent>
            <TabsContent value="quarterly" className="sr-only"></TabsContent>
            <TabsContent value="yearly" className="sr-only"></TabsContent>
            <TabsContent value="custom" className="sr-only"></TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
