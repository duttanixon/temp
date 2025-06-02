"use client";

import { useState, useMemo } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { formatDistanceToNow } from "date-fns";
import { ja } from "date-fns/locale";
import { Device } from "@/types/device";
import DeviceStatusBadge from "../_components/DeviceStatusBadge";
import { ChevronDown, ChevronUp } from "lucide-react";

type DeviceTableProps = {
  initialDevices: Device[];
};

type SortKey = "name" | "device_type" | "customer_name" | "status";
type SortDirection = "asc" | "desc";

export default function DeviceTable({ initialDevices }: DeviceTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>("name");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");
  const router = useRouter();
  const searchParams = useSearchParams();

  const handleSort = (key: SortKey) => {
    if (key === sortKey) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDirection("asc");
    }
  };

  const filteredAndSortedDevices = useMemo(() => {
    const deviceType = searchParams.get("deviceType");
    const status = searchParams.get("status");

    const filtered = initialDevices.filter((device) => {
      const matchesDeviceType =
        !deviceType || device.device_type === deviceType;
      const matchesStatus = !status || device.status === status;
      return matchesDeviceType && matchesStatus;
    });

    return filtered.sort((a, b) => {
      const valA = (a[sortKey] || "").toString().toLowerCase();
      const valB = (b[sortKey] || "").toString().toLowerCase();
      if (valA < valB) return sortDirection === "asc" ? -1 : 1;
      if (valA > valB) return sortDirection === "asc" ? 1 : -1;
      return 0;
    });
  }, [initialDevices, sortKey, sortDirection, searchParams]);

  const renderSortIcon = (key: SortKey) => {
    return sortKey === key ? (
      sortDirection === "asc" ? (
        <ChevronUp size={16} />
      ) : (
        <ChevronDown size={16} />
      )
    ) : null;
  };

  return (
    <div className="overflow-x-auto rounded-lg border border-[#BDC3C7]">
      <table className="w-full min-w-[800px]">
        <colgroup>
          <col className="w-1/5" />
          <col className="w-1/5" />
          <col className="w-1/5" />
          <col className="w-1/10" />
          <col className="w-1/5" />
          <col className="w-1/10" />
        </colgroup>
        <thead className="bg-[#ECF0F1]">
          <tr>
            <th
              onClick={() => handleSort("name")}
              className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50] cursor-pointer"
            >
              <div className="flex justify-center items-center gap-1 select-none">
                <span>名前</span>
                {renderSortIcon("name")}
              </div>
            </th>
            <th
              onClick={() => handleSort("device_type")}
              className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50] cursor-pointer"
            >
              <div className="flex justify-center items-center gap-1 select-none">
                <span>タイプ</span>
                {renderSortIcon("device_type")}
              </div>
            </th>
            <th
              onClick={() => handleSort("customer_name")}
              className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50] cursor-pointer"
            >
              <div className="flex justify-center items-center gap-1 select-none">
                <span>顧客名</span>
                {renderSortIcon("customer_name")}
              </div>
            </th>
            <th
              onClick={() => handleSort("status")}
              className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50] cursor-pointer"
            >
              <div className="flex justify-center items-center gap-1 select-none">
                <span>ステータス</span>
                {renderSortIcon("status")}
              </div>
            </th>
            <th className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50]">
              最終接続
            </th>
            <th className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50]">
              アクション
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-[#BDC3C7]">
          {filteredAndSortedDevices.length > 0 ? (
            filteredAndSortedDevices.map((device) => (
              <tr
                key={device.device_id}
                onClick={() => router.push(`/devices/${device.device_id}`)}
                className="border-t cursor-pointer hover:bg-[#F9F9F9] transition-colors duration-150 bg-white"
              >
                <td className="px-6 py-3 text-sm text-[#2C3E50] max-w-0">
                  <div className="truncate">{device.name}</div>
                </td>
                <td className="px-6 py-3 text-sm text-[#2C3E50] whitespace-nowrap text-center">
                  {device.device_type}
                </td>
                <td className="px-6 py-3 text-sm text-[#2C3E50] text-center max-w-0">
                  <div className="truncate">{device.customer_name || "-"}</div>
                </td>
                <td className="px-6 py-3 text-sm text-center">
                  <DeviceStatusBadge
                    status={device.status}
                    isOnline={device.is_online}
                  />
                </td>
                <td className="px-6 py-3 text-sm text-[#2C3E50] text-center whitespace-nowrap">
                  {device.last_connected
                    ? formatDistanceToNow(new Date(device.last_connected), {
                        addSuffix: true,
                        locale: ja,
                      })
                    : "-"}
                </td>
                <td className="px-6 py-3 text-sm text-[#2C3E50] text-center">
                  <span className="px-2 py-1">-</span>
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td
                colSpan={6}
                className="px-6 py-4 text-center text-sm text-[#7F8C8D]"
              >
                デバイスが見つかりません
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
