"use client";

import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { deviceSolutionService } from "@/services/deviceSolutionService";
import { AlertCircle, Loader2 } from "lucide-react";
import React, { useEffect, useState } from "react";
import { FilterCard } from "./FilterCard";

interface DeviceInfo {
  device_id: string;
  device_name?: string;
  device_location?: string;
  customer_id?: string;
}

interface DevicesFilterDirectionProps {
  solutionId: string;
  selectedDevices: string[];
  onSelectionChange: (selectedDevices: string[]) => void;
  customerId?: string[];
  userCustomerId?: string;
  icon?: React.ReactNode;
  iconBgColor?: string;
  collapsible?: boolean;
  defaultExpanded?: boolean;
}

export function DevicesDirectionFilter({
  solutionId,
  selectedDevices,
  onSelectionChange,
  customerId,
  userCustomerId,
  icon,
  iconBgColor,
  collapsible = false,
  defaultExpanded = true,
}: DevicesFilterDirectionProps) {
  console.log("customer_id:", customerId);
  const [availableDevices, setAvailableDevices] = useState<DeviceInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const isAllSelected =
    availableDevices.length > 0 &&
    selectedDevices.length === availableDevices.length;

  const selectionSummary = `(${selectedDevices.length}/${availableDevices.length})`;
  useEffect(() => {
    const fetchDevicesForSolution = async () => {
      if (!solutionId) {
        setIsLoading(false);
        setAvailableDevices([]);
        setError(null);
        return;
      }

      setIsLoading(true);
      setError(null);
      try {
        const devicesData =
          await deviceSolutionService.getDevicesBySolution(solutionId);
        console.log("Fetched devices data:", devicesData);

        const mappedDevicesData = devicesData.map((d) => ({
          device_id: d.device_id,
          device_name: d.device_name,
          device_location: d.device_location,
          customer_id: d.customer_id,
        }));

        // customerIdが指定されている場合、customerIDと紐づいたデバイスのみを選択
        // それ以外はuserCustomerIdに紐づくデバイスを選択
        const filteredDevices =
          customerId && customerId.length > 0
            ? mappedDevicesData.filter((device) =>
                customerId.includes(device.customer_id || "")
              )
            : userCustomerId
              ? mappedDevicesData.filter(
                  (device) => device.customer_id === userCustomerId
                )
              : [];
        setAvailableDevices(filteredDevices);

        if (selectedDevices.length === 0 && filteredDevices.length > 0) {
          onSelectionChange(filteredDevices.map((d) => d.device_id));
          return; // 以降の選択状態調整はスキップ
        }

        // filteredDevicesに基づいて選択されたデバイスを更新(存在しないdevice_idを除外)
        const validSelectedDevices = selectedDevices.filter((id) =>
          filteredDevices.some((d) => d.device_id === id)
        );
        if (validSelectedDevices.length !== selectedDevices.length) {
          onSelectionChange(validSelectedDevices);
        } else if (filteredDevices.length === 0 && selectedDevices.length > 0) {
          console.log(
            "DevicesFilter: No devices available for this solution, clearing selection."
          );
          onSelectionChange([]);
        }
      } catch (error) {
        console.error("Failed to fetch devices for solution:", error);
        setError("デバイスの読み込みに失敗しました");
        setAvailableDevices([]);
        if (selectedDevices.length > 0) {
          onSelectionChange([]);
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchDevicesForSolution();
  }, [solutionId, customerId]);

  const handleDeviceToggle = (deviceId: string) => {
    const newSelectedDevices = selectedDevices.includes(deviceId)
      ? selectedDevices.filter((d) => d !== deviceId)
      : [...selectedDevices, deviceId];
    onSelectionChange(newSelectedDevices);
  };

  const handleSelectAllToggle = () => {
    if (isAllSelected) {
      onSelectionChange([]);
    } else {
      onSelectionChange(availableDevices.map((d) => d.device_id));
    }
  };

  const renderContent = () => {
    if (isLoading) {
      return (
        <div className="flex items-center justify-center py-8">
          <div className="flex flex-col items-center gap-2">
            <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
            <span className="text-sm text-slate-500">
              デバイスを読み込み中...
            </span>
          </div>
        </div>
      );
    }

    if (error) {
      return (
        <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
          <AlertCircle className="h-4 w-4 text-red-500 flex-shrink-0" />
          <span className="text-sm text-red-700">{error}</span>
        </div>
      );
    }

    if (availableDevices.length === 0) {
      return (
        <div className="flex items-center gap-2 p-3 bg-amber-50 border border-amber-200 rounded-lg">
          <AlertCircle className="h-4 w-4 text-amber-500 flex-shrink-0" />
          <span className="text-sm text-amber-700">
            このソリューションに紐づく利用可能なデバイスがありません。
          </span>
        </div>
      );
    }

    return (
      <div className="space-y-3">
        {/* Select All Option */}
        <div className="flex items-center space-x-2 p-1 hover:bg-slate-50 rounded-lg transition-colors duration-200 group">
          <Checkbox
            id="select-all-devices"
            checked={isAllSelected}
            onCheckedChange={handleSelectAllToggle}
            className="data-[state=checked]:bg-blue-500 data-[state=checked]:border-blue-500 cursor-pointer"
          />
          <Label
            htmlFor="select-all-devices"
            className="text-sm font-medium text-slate-700 group-hover:text-slate-900 cursor-pointer"
          >
            すべて
          </Label>
        </div>

        {/* Individual Device Options */}
        <div>
          <div className="text-xs text-slate-500 font-medium mb-2">
            個別選択:
          </div>
          <ScrollArea className="max-h-40">
            <div className="space-y-1 pr-3">
              {availableDevices.map((device) => {
                const displayName = `${device.device_location || "N/A"}_${device.device_name || "Unknown"}`;

                return (
                  <div
                    key={device.device_id}
                    className="flex items-center space-x-2 p-1 hover:bg-slate-50 rounded-lg transition-colors duration-200 group"
                  >
                    <Checkbox
                      id={`device-${device.device_id}`}
                      checked={selectedDevices.includes(device.device_id)}
                      onCheckedChange={() =>
                        handleDeviceToggle(device.device_id)
                      }
                      className="data-[state=checked]:bg-blue-500 data-[state=checked]:border-blue-500 cursor-pointer"
                    />
                    <Label
                      htmlFor={`device-${device.device_id}`}
                      className="text-sm text-slate-600 group-hover:text-slate-800 cursor-pointer transition-colors truncate"
                      title={displayName}
                    >
                      {displayName}
                    </Label>
                  </div>
                );
              })}
            </div>
          </ScrollArea>
        </div>
      </div>
    );
  };

  return (
    <FilterCard
      title="デバイス"
      icon={icon}
      iconBgColor={iconBgColor}
      collapsible={collapsible}
      defaultExpanded={defaultExpanded}
      selectionSummary={selectionSummary}
    >
      {renderContent()}
    </FilterCard>
  );
}
