/*
 * This component list all the devices based on application, common accross all application
 */

"use client";

import { useBatchDeviceStatus } from "@/hooks/useBatchDeviceStatus";
import { Device } from "@/types/device";
import { Solution } from "@/types/solution";
import { type FC, type ReactNode, useMemo, useState } from "react";
import { DeviceTableHeader } from "./DeviceTableHeader";
import { DeviceTableRow } from "./DeviceTableRow";

type SortKey = "name" | "device_type" | "customer_name" | "solution_name";
type SortDirection = "asc" | "desc";

type DeviceTableProps = {
  children?: ReactNode;
  devices?: Device[];
  solution?: Solution;
  isShowInactive?: boolean;
};

/**
 * DeviceTable Component
 */
export const DeviceTable: FC<DeviceTableProps> = ({
  devices = [],
  solution,
  isShowInactive = false,
}) => {
  console.log("solution in DeviceTable:", solution);
  const [sortKey, setSortKey] = useState<SortKey>("name");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");

  // Get all device IDs for batch status fetch
  const deviceIds = useMemo(
    () => devices.map((device) => device.device_id),
    [devices]
  );

  // Fetch statuses for all devices at once
  const { statuses } = useBatchDeviceStatus(deviceIds, {
    refetchInterval: 60000, // Refresh every minute
    enabled: deviceIds.length > 0,
  });

  const handleSort = (key: SortKey) => {
    if (key === sortKey) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDirection("asc");
    }
  };

  const filteredAndSortedDevices = useMemo(() => {
    // Filter devices based on inactive visibility
    const filtered = devices.filter(
      (device) => isShowInactive || device.status !== "INACTIVE"
    );

    // Sort devices
    return filtered.sort((a, b) => {
      const valA = (a[sortKey] || "").toString().toLowerCase();
      const valB = (b[sortKey] || "").toString().toLowerCase();
      if (valA < valB) return sortDirection === "asc" ? -1 : 1;
      if (valA > valB) return sortDirection === "asc" ? 1 : -1;
      return 0;
    });
  }, [devices, sortKey, sortDirection, isShowInactive]);

  return (
    <div className="overflow-x-auto rounded-lg border border-[#BDC3C7]">
      <table className="w-full min-w-[1000px] divide-y divide-[#BDC3C7]">
        <thead className="bg-[#ECF0F1]">
          <DeviceTableHeader
            sortKey={sortKey}
            sortDirection={sortDirection}
            onSort={handleSort}
          />
        </thead>
        <tbody className="bg-white divide-y divide-[#BDC3C7]">
          {filteredAndSortedDevices.length > 0 ? (
            filteredAndSortedDevices.map((device) => (
              <DeviceTableRow
                key={device.device_id}
                device={device}
                solution={solution as Solution}
                statusInfo={statuses[device.device_id]}
              />
            ))
          ) : (
            <tr>
              <td
                colSpan={7}
                className="px-6 py-4 text-center text-sm text-[#7F8C8D]">
                デバイスが見つかりません
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
};