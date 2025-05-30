"use client";

import React from "react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import SolutionInfoCard from "./SolutionInfoCard";
import CustomerAssignmentsTab from "./CustomerAssignmentsTab";
import DeviceDeploymentsTab from "./DeviceDeploymentsTab";
import { Solution } from "@/types/solution";

interface SolutionDetailsTabsProps {
  solution: Solution;
}

export default function SolutionDetailsTabs({
  solution,
}: SolutionDetailsTabsProps) {
  return (
    <Tabs defaultValue="info" className="w-full">
      <TabsList className="grid w-fit h-full grid-cols-3 bg-white border border-[#BDC3C7] overflow-hidden">
        <TabsTrigger
          value="info"
          className="min-w-[115px] data-[state=active]:bg-[#3498DB] data-[state=active]:text-white data-[state=inactive]:text-gray-600 hover:cursor-pointer py-2"
        >
          情報
        </TabsTrigger>
        <TabsTrigger
          value="customers"
          className="min-w-[115px] data-[state=active]:bg-[#3498DB] data-[state=active]:text-white data-[state=inactive]:text-gray-600 hover:cursor-pointer py-2"
        >
          顧客アサイン
        </TabsTrigger>
        <TabsTrigger
          value="devices"
          className="min-w-[115px] data-[state=active]:bg-[#3498DB] data-[state=active]:text-white data-[state=inactive]:text-gray-600 hover:cursor-pointer py-2"
        >
          デバイスデプロイ
        </TabsTrigger>
      </TabsList>

      <TabsContent value="info">
        <SolutionInfoCard solution={solution} />
      </TabsContent>

      <TabsContent value="customers">
        <CustomerAssignmentsTab solution={solution} />
      </TabsContent>

      <TabsContent value="devices">
        <DeviceDeploymentsTab solution={solution} />
      </TabsContent>
    </Tabs>
  );
}
