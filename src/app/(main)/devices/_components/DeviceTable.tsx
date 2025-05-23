
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { formatDistanceToNow } from "date-fns";
import { ja } from "date-fns/locale";
import { Device } from "@/types/device";
import DeviceStatusBadge from "../_components/DeviceStatusBadge";
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

export default function DeviceTableShadcn({ initialDevices }: DeviceTableProps) {
  const [devices] = useState<Device[]>(initialDevices);
  const router = useRouter();

  const handleViewDetails = (deviceId: string) => {
    router.push(`/devices/${deviceId}`);
  };

  return (
    <div className="rounded-lg border border-[#BDC3C7] overflow-hidden">
      <Table>
        <TableHeader className="bg-[#ECF0F1]">
          <TableRow className="border-b border-[#BDC3C7]">
            <TableHead className="text-sm font-semibold text-[#2C3E50] h-14 py-4">名前</TableHead>
            <TableHead className="text-sm font-semibold text-[#2C3E50] h-14 py-4">タイプ</TableHead>
            <TableHead className="text-sm font-semibold text-[#2C3E50] h-14 py-4">顧客名</TableHead>
            <TableHead className="text-sm font-semibold text-[#2C3E50] h-14 py-4">ステータス</TableHead>
            <TableHead className="text-sm font-semibold text-[#2C3E50] h-14 py-4">最終接続</TableHead>
            <TableHead className="text-sm font-semibold text-[#2C3E50] text-right h-14 py-4">アクション</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody className="bg-white">
          {devices.length > 0 ? (
            devices.map((device) => (
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
                  <DeviceStatusBadge status={device.status} isOnline={device.is_online} />
                </TableCell>
                <TableCell className="text-sm text-[#2C3E50] whitespace-nowrap py-4 h-14">
                  {device.last_connected
                    ? formatDistanceToNow(new Date(device.last_connected), {
                        addSuffix: true,
                        locale: ja,
                      })
                    : "-"}
                </TableCell>
                <TableCell className="text-right py-4 h-14">
                  -
                </TableCell>
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={6} className="text-center text-sm text-[#7F8C8D] py-4">
                デバイスが見つかりません
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}
