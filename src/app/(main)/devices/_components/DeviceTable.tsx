"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { formatDistanceToNow } from "date-fns";
import { ja } from "date-fns/locale";

type Device = {
  device_id: string;
  name: string;
  device_type: string;
  status: string;
  is_online: boolean;
  last_connected?: string;
  customer_id: string;
};

type DeviceTableProps = {
  initialDevices: Device[];
};

export default function DeviceTable({ initialDevices }: DeviceTableProps) {
  const [devices] = useState<Device[]>(initialDevices);
  const router = useRouter();

  const getStatusColor = (status: string, isOnline: boolean) => {
    if (isOnline) return "bg-green-500";

    switch (status) {
      case "ACTIVE":
        return "bg-blue-500";
      case "PROVISIONED":
        return "bg-yellow-500";
      case "INACTIVE":
        return "bg-gray-500";
      case "MAINTENANCE":
        return "bg-orange-500";
      case "DECOMMISSIONED":
        return "bg-red-500";
      default:
        return "bg-gray-500";
    }
  };

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
                  <span className="inline-flex items-center">
                    <span
                      className={`h-2.5 w-2.5 rounded-full ${getStatusColor(device.status, device.is_online)} mr-2`}
                    ></span>
                    <span className="text-sm text-[#2C3E50]">
                      {device.status}
                    </span>
                  </span>
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
