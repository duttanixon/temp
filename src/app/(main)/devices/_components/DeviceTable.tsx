"use client";

import { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { formatDistanceToNow } from "date-fns";
import { ja } from "date-fns/locale";
import { Device } from "@/types/device";
import DeviceStatusBadge from "../_components/DeviceStatusBadge";
import { ChevronDown, ChevronUp } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

type DeviceTableProps = {
  initialDevices: Device[];
};

type SortKey = "name" | "device_type" | "customer_name" | "status";
type SortDirection = "asc" | "desc";

export default function DeviceTableShadcn({
  initialDevices,
}: DeviceTableProps) {
  // const [devices] = useState<Device[]>(initialDevices);
  const [sortKey, setSortKey] = useState<SortKey>("name");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");
  const router = useRouter();

  const handleViewDetails = (deviceId: string) => {
    router.push(`/devices/${deviceId}`);
  };

  const handleSort = (key: SortKey) => {
    if (key === sortKey) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDirection("asc");
    }
  };

  const sortedDevices = useMemo(() => {
    return [...initialDevices].sort((a, b) => {
      const valA = (a[sortKey] || "").toString().toLowerCase();
      const valB = (b[sortKey] || "").toString().toLowerCase();
      if (valA < valB) return sortDirection === "asc" ? -1 : 1;
      if (valA > valB) return sortDirection === "asc" ? 1 : -1;
      return 0;
    });
  }, [initialDevices, sortKey, sortDirection]);

  const renderSortIndicator = (key: SortKey) => {
    if (key !== sortKey) return null;
    return sortDirection === "asc" ? (
      <ChevronUp className="inline w-4 h-4 ml-1" />
    ) : (
      <ChevronDown className="inline w-4 h-4 ml-1" />
    );
  };

  return (
    <div className="rounded-lg border border-[#BDC3C7] overflow-hidden">
      <Table>
        <TableHeader className="bg-[#ECF0F1]">
          <TableRow className="border-b border-[#BDC3C7]">
            <TableHead
              onClick={() => handleSort("name")}
              className="text-sm font-semibold text-[#2C3E50] h-14 py-4 cursor-pointer select-none"
            >
              <div className="flex items-center">
                名前{renderSortIndicator("name")}
              </div>
            </TableHead>
            <TableHead
              onClick={() => handleSort("device_type")}
              className="text-sm font-semibold text-[#2C3E50] h-14 py-4 cursor-pointer select-none"
            >
              <div className="flex items-center">
                タイプ{renderSortIndicator("device_type")}
              </div>
            </TableHead>
            <TableHead
              onClick={() => handleSort("customer_name")}
              className="text-sm font-semibold text-[#2C3E50] h-14 py-4 cursor-pointer select-none"
            >
              <div className="flex items-center">
                顧客名{renderSortIndicator("customer_name")}
              </div>
            </TableHead>
            <TableHead
              onClick={() => handleSort("status")}
              className="text-sm font-semibold text-[#2C3E50] h-14 py-4 cursor-pointer select-none"
            >
              <div className="flex items-center">
                ステータス{renderSortIndicator("status")}
              </div>
            </TableHead>
            <TableHead className="text-sm font-semibold text-[#2C3E50] h-14 py-4">
              最終接続
            </TableHead>
            <TableHead className="text-sm font-semibold text-[#2C3E50] text-right h-14 py-4">
              アクション
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody className="bg-white">
          {sortedDevices.length > 0 ? (
            sortedDevices.map((device) => (
              <TableRow
                key={device.device_id}
                className="hover:bg-[#F8F9FA] cursor-pointer transition-colors border-b border-[#BDC3C7]"
                onClick={() => handleViewDetails(device.device_id)}
              >
                <TableCell className="text-sm text-[#2C3E50] py-4 h-14">
                  {device.name}
                </TableCell>
                <TableCell className="text-sm text-[#2C3E50] whitespace-nowrap py-4 h-14">
                  {device.device_type}
                </TableCell>
                <TableCell className="text-sm text-[#2C3E50] py-4 h-14">
                  {device.customer_name || "-"}
                </TableCell>
                <TableCell className="py-4 h-14">
                  <DeviceStatusBadge
                    status={device.status}
                    isOnline={device.is_online}
                  />
                </TableCell>
                <TableCell className="text-sm text-[#2C3E50] whitespace-nowrap py-4 h-14">
                  {device.last_connected
                    ? formatDistanceToNow(new Date(device.last_connected), {
                        addSuffix: true,
                        locale: ja,
                      })
                    : "-"}
                </TableCell>
                <TableCell className="text-right py-4 h-14">-</TableCell>
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell
                colSpan={6}
                className="text-center text-sm text-[#7F8C8D] py-4"
              >
                デバイスが見つかりません
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}
