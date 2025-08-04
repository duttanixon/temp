/*
 * This component list all table rows for the device table, common accross all application
 */

"use client";

import { Checkbox } from "@/components/ui/checkbox";
import { Device, DeviceStatusInfo } from "@/types/device";
import { Solution } from "@/types/solution";
import { formatDistanceToNow } from "date-fns";
import { ja } from "date-fns/locale";
import { useRouter } from "next/navigation";
import { type FC } from "react";

type DeviceTableRowProps = {
  device: Device;
  solution: Solution;
  statusInfo?: DeviceStatusInfo;
  isSelected: boolean;
  onSelect: (deviceId: string, checked: boolean) => void;
};

/**
 * DeviceTableRow Component
 */
export const DeviceTableRow: FC<DeviceTableRowProps> = ({
  device,
  solution,
  statusInfo,
  isSelected,
  onSelect,
}) => {
  const router = useRouter();

  const handleViewDetails = () => {
    router.push(`/devices/${solution?.solution_id}/${device.device_id}/detail`);
  };

  const isActive = device.status === "ACTIVE";

  // Get status display
  const getStatusDisplay = () => {
    // Use real-time status if available
    if (statusInfo) {
      const isOnline = statusInfo.is_online;
      const lastSeen = statusInfo.last_seen || device.last_connected;

      return (
        <div className="flex items-center justify-center gap-2">
          <span
            className={`inline-block w-2 h-2 rounded-full ${
              isOnline ? "bg-green-500" : "bg-gray-400"
            }`}
            title={isOnline ? "オンライン" : "オフライン"}
          />
          {!isOnline && lastSeen && (
            <span className="text-sm text-gray-600">
              {formatDistanceToNow(new Date(lastSeen), {
                addSuffix: true,
                locale: ja,
              })}
            </span>
          )}
        </div>
      );
    }
    // Fallback to device's last_connected if no status info
    return <div>-</div>;
  };

  // Get solution display
  const getSolutionDisplay = () => {
    if (device.solution_name) {
      return (
        <div className="flex flex-col items-center">
          <div className="font-medium">{device.solution_name}</div>
          {device.solution_version && (
            <div className="text-xs text-gray-500">
              {device.solution_version}
            </div>
          )}
        </div>
      );
    }
    return <div>-</div>;
  };

  // Get job status display
  const getJobDisplay = () => {
    if (device.latest_job_type) {
      // Map job status to appropriate colors
      const getStatusColor = (status?: string) => {
        switch (status) {
          case "QUEUED":
            return "bg-blue-100 text-blue-800";
          case "IN_PROGRESS":
            return "bg-yellow-100 text-yellow-800";
          case "SUCCEEDED":
            return "bg-green-100 text-green-800";
          case "FAILED":
            return "bg-red-100 text-red-800";
          case "TIMED_OUT":
            return "bg-orange-100 text-orange-800";
          case "CANCELED":
            return "bg-gray-100 text-gray-800";
          default:
            return "bg-gray-100 text-gray-800";
        }
      };

      // Map job type to display name
      const getJobTypeName = (type?: string) => {
        switch (type) {
          case "RESTART_APPLICATION":
            return "アプリ再起動";
          case "REBOOT_DEVICE":
            return "デバイス再起動";
          default:
            return type || "-";
        }
      };

      return (
        <div className="flex flex-col items-center gap-1">
          <div className="text-sm font-medium">
            {getJobTypeName(device.latest_job_type)}
          </div>
          {device.latest_job_status && (
            <span
              className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(
                device.latest_job_status
              )}`}
            >
              {device.latest_job_status}
            </span>
          )}
        </div>
      );
    }
    return <div>-</div>;
  };

  return (
    <tr
      onClick={handleViewDetails}
      className={
        isActive
          ? "cursor-pointer hover:bg-[#F9F9F9] transition-colors duration-150 bg-white"
          : "cursor-pointer bg-gray-50/50 hover:bg-gray-100/50 transition-colors duration-150"
      }
    >
      <td className="px-6 py-3 text-center">
        <Checkbox
          checked={isSelected}
          onCheckedChange={(checked) => onSelect(device.device_id, !!checked)}
          onClick={(e) => e.stopPropagation()}
          className="w-5 h-5 border-gray-400"
        />
      </td>
      <td className="px-6 py-3 text-sm text-[#2C3E50] max-w-0 text-center">
        <div className="truncate">{device.name}</div>
      </td>
      <td className="px-6 py-3 text-sm text-[#2C3E50] whitespace-nowrap text-center">
        {device.device_type}
      </td>
      <td className="px-6 py-3 text-sm text-[#2C3E50] text-center max-w-0">
        <div className="truncate">{device.customer_name || "-"}</div>
      </td>
      <td className="px-6 py-3 text-sm text-[#2C3E50] text-center">
        {getSolutionDisplay()}
      </td>
      <td className="px-6 py-3 text-xs text-[#2C3E50] text-center">
        {getJobDisplay()}
      </td>
      <td className="px-6 py-3 text-sm text-[#2C3E50] text-center whitespace-nowrap">
        {getStatusDisplay()}
      </td>
    </tr>
  );
};
