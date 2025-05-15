"use client";

import React, { useState } from 'react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import SolutionInfoCard from '../_components/SolutionInfoCard';
import CustomerAssignmentsTab from './CustomerAssignmentsTab';
import DeviceDeploymentsTab from './DeviceDeploymentsTab';
import { Solution } from '@/types/solution';

interface SolutionDetailsTabsProps {
  solution: Solution;
}

export default function SolutionDetailsTabs({ solution }: SolutionDetailsTabsProps) {
  return (
    <Tabs defaultValue="info" className="w-full">
      <TabsList className="bg-white rounded-lg border border-[#BDC3C7] p-1 flex mb-4">
        <TabsTrigger 
          value="info" 
          className="flex-1 py-2 px-4 data-[state=active]:bg-[#3498DB] data-[state=active]:text-white"
        >
          情報
        </TabsTrigger>
        <TabsTrigger 
          value="customers" 
          className="flex-1 py-2 px-4 data-[state=active]:bg-[#3498DB] data-[state=active]:text-white"
        >
          顧客アサイン
        </TabsTrigger>
        <TabsTrigger 
          value="devices" 
          className="flex-1 py-2 px-4 data-[state=active]:bg-[#3498DB] data-[state=active]:text-white"
        >
          デバイスデプロイ
        </TabsTrigger>
      </TabsList>
      
      <TabsContent value="info" className="mt-0">
        <SolutionInfoCard solution={solution} />
      </TabsContent>
      
      <TabsContent value="customers" className="mt-0">
        <CustomerAssignmentsTab solution={solution} />
      </TabsContent>
      
      <TabsContent value="devices" className="mt-0">
        <DeviceDeploymentsTab solution={solution} />
      </TabsContent>
    </Tabs>
  );
}