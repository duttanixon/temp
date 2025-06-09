"use client";

import React, { useState, useEffect } from "react";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { FilterCard } from "./FilterCard";
import { ScrollArea } from "@/components/ui/scroll-area";
import { deviceSolutionService } from "@/services/deviceSolutionService";

interface DeviceInfo {
  // Local type for fetched devices
  device_id: string;
  device_name?: string;
  device_location?: string;
}

interface DevicesFilterProps {
  solutionId: string; // solutionId is crucial for fetching relevant devices
  selectedDevices: string[];
  onSelectionChange: (selectedDevices: string[]) => void;
}

export function DevicesFilter({
  solutionId,
  selectedDevices,
  onSelectionChange,
}: DevicesFilterProps) {
  const [availableDevices, setAvailableDevices] = useState<DeviceInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  // isAllSelected can be derived directly
  const isAllSelected =
    availableDevices.length > 0 &&
    selectedDevices.length === availableDevices.length;

  useEffect(() => {
    const fetchDevicesForSolution = async () => {
      if (!solutionId) {
        setIsLoading(false);
        setAvailableDevices([]);
        // If solutionId is not yet available, do not clear selected devices from parent
        // onSelectionChange([]); // Potentially clears selection if solutionId briefly becomes null
        // Do not clear selectedDevices here, parent (CityEyeClient) will manage reset on solutionId change
        return;
      }
      setIsLoading(true);
      try {
        // getDevicesBySolution return a list of devices relevant to the solution.
        const devicesData =
          await deviceSolutionService.getDevicesBySolution(solutionId);
        const mappedDevicesData = devicesData.map((d) => ({
          device_id: d.device_id,
          device_name: d.device_name,
          device_location: d.device_location,
        }));
        setAvailableDevices(mappedDevicesData);

        // If devices were fetched and no devices are currently selected from parent state,
        // auto-select all fetched devices.
        if (mappedDevicesData.length > 0 && selectedDevices.length === 0) {
          console.log("DevicesFilter: Auto-selecting all available devices.");
          onSelectionChange(mappedDevicesData.map((d) => d.device_id));
        } else if (
          mappedDevicesData.length === 0 &&
          selectedDevices.length > 0
        ) {
          // If no devices are available for the new solutionId, clear any existing selection.
          console.log(
            "DevicesFilter: No devices available for this solution, clearing selection."
          );
          onSelectionChange([]);
        }
      } catch (error) {
        console.error("Failed to fetch devices for solution:", error);
        setAvailableDevices([]);
        if (selectedDevices.length > 0) {
          // Clear selection if fetch fails
          onSelectionChange([]);
        }
      } finally {
        setIsLoading(false);
      }
    };
    fetchDevicesForSolution();
  }, [solutionId]); // Re-fetch if solutionId changes

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

  if (isLoading) {
    return (
      <FilterCard title="デバイス">
        <div className="text-sm text-gray-500">デバイスを読み込み中...</div>
      </FilterCard>
    );
  }

  return (
    <FilterCard title="デバイス">
      <div className="space-y-2">
        {availableDevices.length > 0 ? (
          <>
            <div className="flex items-center space-x-2">
              <Checkbox
                id="select-all-devices"
                checked={isAllSelected}
                onCheckedChange={handleSelectAllToggle}
                className="cursor-pointer"
              />
              <Label
                htmlFor="select-all-devices"
                className="text-sm font-medium cursor-pointer"
              >
                すべて
              </Label>
            </div>
            <ScrollArea className="h-32">
              <div className="space-y-1 pr-3">
                {availableDevices.map((device) => (
                  <div
                    key={device.device_id}
                    className="flex items-center space-x-2"
                  >
                    <Checkbox
                      id={`device-${device.device_id}`}
                      checked={selectedDevices.includes(device.device_id)}
                      onCheckedChange={() =>
                        handleDeviceToggle(device.device_id)
                      }
                      className="cursor-pointer"
                    />
                    <Label
                      htmlFor={`device-${device.device_id}`}
                      className="text-sm font-normal truncate cursor-pointer"
                      title={`${device.device_location || "N/A"}_${device.device_name || "Unknown"}`}
                    >
                      {`${device.device_location || "N/A"}_${device.device_name || "Unknown"}`}
                    </Label>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </>
        ) : (
          <div className="text-sm text-gray-500">
            このソリューションに紐づく利用可能なデバイスがありません。
          </div>
        )}
      </div>
    </FilterCard>
  );
}
