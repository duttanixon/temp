"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { formatDistanceToNow } from "date-fns";
import { ja } from "date-fns/locale";
import { Device, DeviceStatus } from "@/types/device";
import DeviceStatusBadge from "../_components/DeviceStatusBadge";

type DeviceTableProps = {
  initialDevices: Device[];
};

export default function DeviceTable({ initialDevices }: DeviceTableProps) {
  const [devices] = useState<Device[]>(initialDevices);
  const router = useRouter();

  const handleViewDetails = (deviceId: string) => {
    router.push(`/devices/${deviceId}`);
  };

  return (
    <div className="overflow-x-auto rounded-lg border border-[#BDC3C7]">
      <table className="min-w-full divide-y divide-[#BDC3C7]">
        <thead className="bg-[#ECF0F1]">
          <tr>
            <th
              scope="col"
              className="px-6 py-3 text-left text-sm font-semibold text-[#2C3E50]"
            >
              名前
            </th>
            <th
              scope="col"
              className="px-6 py-3 text-left text-sm font-semibold text-[#2C3E50]"
            >
              タイプ
            </th>
            <th
              scope="col"
              className="px-6 py-3 text-left text-sm font-semibold text-[#2C3E50]"
            >
              ステータス
            </th>
            <th
              scope="col"
              className="px-6 py-3 text-left text-sm font-semibold text-[#2C3E50]"
            >
              最終接続
            </th>
            <th
              scope="col"
              className="px-6 py-3 text-right text-sm font-semibold text-[#2C3E50]"
            >
              アクション
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-[#BDC3C7]">
          {devices.length > 0 ? (
            devices.map((device) => (
              <tr key={device.device_id} className="hover:bg-[#F8F9FA]">
                <td className="px-6 py-4 whitespace-nowrap text-sm text-[#2C3E50]">
                  {device.name}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-[#2C3E50]">
                  {device.device_type}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <DeviceStatusBadge status={device.status} isOnline={device.is_online} />
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-[#2C3E50]">
                  {device.last_connected
                    ? formatDistanceToNow(new Date(device.last_connected), {
                        addSuffix: true,
                        locale: ja,
                      })
                    : "-"}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                  <button
                    onClick={() => handleViewDetails(device.device_id)}
                    className="text-blue-600 hover:text-blue-800 font-medium"
                  >
                    詳細
                  </button>
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td
                colSpan={5}
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
