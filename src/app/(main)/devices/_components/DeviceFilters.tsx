"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

export default function DeviceFilters() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [deviceType, setDeviceType] = useState(
    searchParams.get("deviceType") || ""
  );
  const [status, setStatus] = useState(searchParams.get("status") || "");

  useEffect(() => {
    const debounce = setTimeout(() => {
      const params = new URLSearchParams();
      if (deviceType) params.set("deviceType", deviceType);
      if (status) params.set("status", status);
      router.push(`/devices?${params.toString()}`);
    }, 300);

    return () => clearTimeout(debounce);
  }, [deviceType, status, router]);

  return (
    <div className="relative border border-gray-400 rounded-md px-4 py-3 w-2/5 bg-white overflow-hidden">
      <div className="flex items-center gap-6 flex-nowrap">
        <label className="text-gray-800 text-sm whitespace-nowrap">
          デバイスタイプ:
        </label>
        <div className="relative w-40">
          <select
            value={deviceType}
            onChange={(e) => setDeviceType(e.target.value)}
            className="w-full bg-white border border-gray-400 rounded-lg px-3 py-1 text-sm text-gray-700 focus:outline-none focus:ring-1 focus:ring-gray-500"
          >
            <option value="">すべて</option>
            <option value="NVIDIA_JETSON">NVIDIA Jetson</option>
            <option value="RASPBERRY_PI">Raspberry Pi</option>
          </select>
        </div>

        <label className="text-gray-800 text-sm whitespace-nowrap">
          ステータス:
        </label>
        <div className="relative w-40">
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="w-full bg-white border border-gray-400 rounded-lg px-3 py-1 text-sm text-gray-700 focus:outline-none focus:ring-1 focus:ring-gray-500"
          >
            <option value="">すべて</option>
            <option value="CREATED">作成済み</option>
            <option value="PROVISIONED">プロビジョン済み</option>
            <option value="ACTIVE">アクティブ</option>
            <option value="INACTIVE">非アクティブ</option>
            <option value="MAINTENANCE">メンテナンス</option>
            <option value="DECOMMISSIONED">廃止</option>
          </select>
        </div>
      </div>
    </div>
  );
}
