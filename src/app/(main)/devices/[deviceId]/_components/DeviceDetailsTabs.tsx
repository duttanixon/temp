"use client";

import { useState } from "react";
import UpdatesTab from "./device-tabs/UpdatesTab";
import PackagesTab from "./device-tabs/PackagesTab";
import MetricsTab from "./device-tabs/MetricsTab";
import RemoteAccessTab from "./device-tabs/RemoteAccessTab";
import { cn } from "@/lib/utils";

export default function DeviceDetailsTabs() {
  const [activeTab, setActiveTab] = useState("metrics");

  const tabs = [
    { id: "metrics", label: "Metrics" },
    { id: "packages", label: "Packages" },
    { id: "updates", label: "Updates" },
    { id: "remoteAccess", label: "Remote Access" },
  ];

  return (
    <div className="w-full">
      <div className="flex ">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "px-4 py-2 font-medium text-sm",
              activeTab === tab.id
                ? "border-b-2 border-[#3498DB] text-[#3498DB]"
                : "text-[#7F8C8D] hover:text-[#2C3E50]"
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div>
        {activeTab === "metrics" && <MetricsTab />}
        {activeTab === "packages" && <PackagesTab />}
        {activeTab === "updates" && <UpdatesTab />}
        {activeTab === "remoteAccess" && <RemoteAccessTab />}
      </div>
    </div>
  );
}
