/*
 * This component list all table rows for the device table, common accross all application
 */

"use client";

import { Device, DeviceStatusInfo } from "@/types/device";
import { Solution } from "@/types/solution";
import { formatDistanceToNow } from "date-fns";
import { ja } from "date-fns/locale";
import { type FC } from "react";
import { solutionDeviceActionComponents } from "./solutionDeviceActionComponents";

type SolutionDeviceTableRowProps = {
  device: Device;
  solution: Solution;
  statusInfo?: DeviceStatusInfo;
};

/**
 * DeviceTableRow Component
 */
export const SolutionDeviceTableRow: FC<SolutionDeviceTableRowProps> = ({
  device,
  solution,
  statusInfo,
}) => {
  // const ActionComponent = deviceActionComponents[solution.name.replace(/\s+/g, '').toLowerCase()]
  const ActionComponent = solution
    ? solutionDeviceActionComponents[
        solution.name.replace(/\s+/g, "").toLowerCase()
      ]
    : null;
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

  return (
    <tr
      className={
        isActive
          ? "hover:bg-[#F9F9F9] transition-colors duration-150 bg-white"
          : "bg-gray-50/50 hover:bg-gray-100/50 transition-colors duration-150"
      }>
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
        {getStatusDisplay()}
      </td>
      <td className="w-[240px]">
        <div className="relative flex items-center justify-center gap-2 px-2">
          <div className="absolute left-0 top-0 h-full border-l border-[#BDC3C7]" />
          {ActionComponent && (
            <ActionComponent device={device} solution={solution} />
          )}
        </div>
      </td>
    </tr>
  );
};
