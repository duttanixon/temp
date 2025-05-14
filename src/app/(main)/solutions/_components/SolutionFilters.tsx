"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

export default function SolutionFilters() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [deviceType, setDeviceType] = useState(
    searchParams.get("deviceType") || ""
  );
  const [status, setStatus] = useState(searchParams.get("status") || "");

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();

    const params = new URLSearchParams();
    if (deviceType) params.set("deviceType", deviceType);
    if (status) params.set("status", status);

    router.push(`/solutions?${params.toString()}`);
  };

  const handleReset = () => {
    setDeviceType("");
    setStatus("");
    router.push("/solutions");
  };

  return (
    <div className="bg-white p-4 rounded-lg border border-[#BDC3C7]">
      <form onSubmit={handleSearch} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label
              htmlFor="deviceType"
              className="block text-sm font-medium text-[#7F8C8D]"
            >
              デバイスタイプ互換性
            </label>
            <select
              id="deviceType"
              value={deviceType}
              onChange={(e) => setDeviceType(e.target.value)}
              className="mt-1 block w-full rounded-md border border-[#BDC3C7] px-3 py-2 text-sm"
            >
              <option value="">すべて</option>
              <option value="NVIDIA_JETSON">NVIDIA Jetson</option>
              <option value="RASPBERRY_PI">Raspberry Pi</option>
            </select>
          </div>

          <div>
            <label
              htmlFor="status"
              className="block text-sm font-medium text-[#7F8C8D]"
            >
              ステータス
            </label>
            <select
              id="status"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="mt-1 block w-full rounded-md border border-[#BDC3C7] px-3 py-2 text-sm"
            >
              <option value="">すべて</option>
              <option value="ACTIVE">有効</option>
              <option value="BETA">ベータ版</option>
              <option value="DEPRECATED">非推奨</option>
            </select>
          </div>
        </div>

        <div className="flex justify-end space-x-2">
          <button
            type="button"
            onClick={handleReset}
            className="px-4 py-2 border border-[#BDC3C7] rounded-md text-sm text-[#7F8C8D] hover:bg-[#ECF0F1]"
          >
            リセット
          </button>
          <button
            type="submit"
            className="px-4 py-2 bg-[#3498DB] text-white rounded-md text-sm hover:bg-[#2980B9]"
          >
            検索
          </button>
        </div>
      </form>
    </div>
  );
}