"use client";

import { type FC } from "react";
import { useRouter } from "next/navigation";
import { formatDistanceToNow } from "date-fns";
import { ja } from "date-fns/locale";
import { Edit } from "lucide-react";
import { Device } from "@/types/device";
import { Solution } from "@/types/solution";

type DeviceTableRowProps = {
  device: Device;
  solution: Solution;
};

/**
 * DeviceTableRow Component
 */
export const DeviceTableRow: FC<DeviceTableRowProps> = ({
  device,
  solution
}) => {
  const router = useRouter();

  const handleViewDetails = () => {
    router.push(`/devices/detail/${device.device_id}`);
  };

  const handleEdit = () => {
    router.push(`/devices/${device.device_id}/edit`);
  };

  const isActive = device.status === "ACTIVE";

  return (
    <tr
      onClick={handleViewDetails}
      className={
        isActive
          ? "cursor-pointer hover:bg-[#F9F9F9] transition-colors duration-150 bg-white"
          : "cursor-pointer bg-gray-50/50 hover:bg-gray-100/50 transition-colors duration-150"
      }
    >
      <td className="px-6 py-3 text-sm text-[#2C3E50] max-w-0 text-center">
        <div className="truncate">{device.name}</div>
      </td>
      <td className="px-6 py-3 text-sm text-[#2C3E50] whitespace-nowrap text-center">
        {device.device_type}
      </td>
      <td className="px-6 py-3 text-sm text-[#2C3E50] text-center max-w-0">
        <div className="truncate">{device.customer_name || "-"}</div>
      </td>
      <td className="px-6 py-3 text-sm text-[#2C3E50] text-center whitespace-nowrap">
        {device.last_connected
          ? formatDistanceToNow(new Date(device.last_connected), {
              addSuffix: true,
              locale: ja,
            })
          : "-"}
      </td>
      <td className="w-[240px]">
        <div className="relative flex items-center justify-center gap-2 px-2">
          <div className="absolute left-0 top-0 h-full border-l border-[#BDC3C7]" />
          {/* Edit Action */}
          <div className="flex size-full items-center justify-center">
            {isActive ? (
              <button
                onClick={handleEdit}
                className="group flex size-[30px] items-center justify-center rounded-full transition-colors duration-300 hover:bg-[#27AE60]"
              >
                <Edit className="text-xl text-[#7F8C8D] transition-colors duration-300 group-hover:text-white" />
              </button>
            ) : (
              <div className="group flex size-[30px] cursor-not-allowed items-center justify-center">
                <Edit className="text-xl text-[#BDC3C7]" />
              </div>
            )}
          </div>
        </div>
      </td>
    </tr>
  );
};