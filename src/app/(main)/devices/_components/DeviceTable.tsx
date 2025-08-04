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
import { Button } from "@/components/ui/button";
import { jobService } from "@/services/jobService";
import { toast } from "sonner";

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
  const [sortKey, setSortKey] = useState<SortKey>("name");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");
  const [selectedDevices, setSelectedDevices] = useState<string[]>([]);

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

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedDevices(devices.map((d) => d.device_id));
    } else {
      setSelectedDevices([]);
    }
  };

  const handleSelectDevice = (deviceId: string, checked: boolean) => {
    if (checked) {
      setSelectedDevices((prev) => [...prev, deviceId]);
    } else {
      setSelectedDevices((prev) => prev.filter((id) => id !== deviceId));
    }
  };

  const handleRestartDevice = async () => {
    try {
      await jobService.createRebootDeviceJob({ device_ids: selectedDevices });
      toast.success("Restart device job created successfully.");
      setSelectedDevices([]);
    } catch (error) {
      toast.error("Failed to create restart device job.");
    }
  };

  const handleRestartApplication = async () => {
      try {
          await jobService.createRestartApplicationJob({ device_ids: selectedDevices });
          toast.success("Restart application job created successfully.");
          setSelectedDevices([]);
      } catch (error) {
          toast.error("Failed to create restart application job.");
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
    <>
      {selectedDevices.length > 0 && (
        <div className="flex gap-2 mb-4">
          <Button onClick={handleRestartDevice}>デバイス再起動</Button>
          <Button onClick={handleRestartApplication}>
            アプリケーション再起動
          </Button>
        </div>
      )}
      <div className="overflow-x-auto rounded-lg border border-[#BDC3C7]">
        <table className="w-full min-w-[1000px] divide-y divide-[#BDC3C7]">
          <thead className="bg-[#ECF0F1]">
              <DeviceTableHeader
                sortKey={sortKey}
                sortDirection={sortDirection}
                onSort={handleSort}
                onCheckedChange={handleSelectAll}
                selectedDevices={selectedDevices}
                devices={devices}
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
                  isSelected={selectedDevices.includes(device.device_id)}
                  onSelect={handleSelectDevice}
                />
              ))
            ) : (
              <tr>
                <td
                  colSpan={8}
                  className="px-6 py-4 text-center text-sm text-[#7F8C8D]"
                >
                  デバイスが見つかりません
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
};