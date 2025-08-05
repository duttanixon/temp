/*
 * This component list all the devices based on application, common accross all application
 */

"use client";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { useBatchDeviceStatus } from "@/hooks/useBatchDeviceStatus";
import { jobService } from "@/services/jobService";
import { Device } from "@/types/device";
import { type FC, type ReactNode, useMemo, useState } from "react";
import { toast } from "sonner";
import { DeviceTableHeader } from "./DeviceTableHeader";
import { DeviceTableRow } from "./DeviceTableRow";

type SortKey =
  | "name"
  | "device_type"
  | "customer_name"
  | "solution_name"
  | "last_connected";
type SortDirection = "asc" | "desc";

type DeviceTableProps = {
  children?: ReactNode;
  devices?: Device[];
  isShowInactive?: boolean;
};

/**
 * DeviceTable Component
 */
export const DeviceTable: FC<DeviceTableProps> = ({
  devices = [],
  isShowInactive = false,
}) => {
  const [sortKey, setSortKey] = useState<SortKey>("name");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");
  const [selectedDevices, setSelectedDevices] = useState<string[]>([]);

  // Dialog
  const [isRestartDeviceDialogOpen, setIsRestartDeviceDialogOpen] =
    useState(false);
  const [isRestartApplicationDialogOpen, setIsRestartApplicationDialogOpen] =
    useState(false);
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
      setIsRestartDeviceDialogOpen(false);
    } catch (error) {
      toast.error("Failed to create restart device job.");
    }
  };

  const handleRestartApplication = async () => {
    try {
      await jobService.createRestartApplicationJob({
        device_ids: selectedDevices,
      });
      toast.success("Restart application job created successfully.");
      setSelectedDevices([]);
      setIsRestartApplicationDialogOpen(false);
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
      <div className="flex gap-2 mb-4">
        <Dialog
          open={isRestartDeviceDialogOpen}
          onOpenChange={setIsRestartDeviceDialogOpen}
        >
          <DialogTrigger asChild>
            <Button disabled={selectedDevices.length === 0}>
              デバイス再起動
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>デバイス再起動の確認</DialogTitle>
            </DialogHeader>
            <DialogDescription>
              選択したデバイスを再起動します。よろしいですか？
            </DialogDescription>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setIsRestartDeviceDialogOpen(false)}
              >
                キャンセル
              </Button>
              <Button onClick={handleRestartDevice}>再起動</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <Dialog
          open={isRestartApplicationDialogOpen}
          onOpenChange={setIsRestartApplicationDialogOpen}
        >
          <DialogTrigger asChild>
            <Button disabled={selectedDevices.length === 0}>
              アプリケーション再起動
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>アプリケーション再起動の確認</DialogTitle>
            </DialogHeader>
            <DialogDescription>
              選択したデバイスのアプリケーションを再起動します。よろしいですか？
            </DialogDescription>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setIsRestartApplicationDialogOpen(false)}
              >
                キャンセル
              </Button>
              <Button onClick={handleRestartApplication}>再起動</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

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
