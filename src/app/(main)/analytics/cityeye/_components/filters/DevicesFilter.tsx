"use client";

import React, { useState, useEffect } from "react";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { FilterCard } from "./FilterCard";
import { ScrollArea } from "@/components/ui/scroll-area";
import { deviceSolutionService } from "@/services/deviceSolutionService";
import { DeviceDeployment } from "@/types/deviceSolution";

interface DevicesFilterProps {
  initialSelectedDevices?: string[];
  onSelectionChange?: (selectedDevices: string[]) => void;
  customerId?: string; // Kept for potential future use, but not directly used in API call for this specific task
  solutionId?: string; // Made solutionId mandatory as it's key for this filter
}

export function DevicesFilter({
  initialSelectedDevices,
  onSelectionChange,
  customerId, // customerId is available if needed by other logic, but getDevicesBySolution filters by current user's customer if not admin
  solutionId,
}: DevicesFilterProps) {
  const [availableDevices, setAvailableDevices] = useState<
    Pick<DeviceDeployment, "device_id" | "device_name" | "device_location">[]
  >([]);
  const [selectedDevices, setSelectedDevices] = useState<string[]>(
    initialSelectedDevices || []
  );
  const [isAllSelected, setIsAllSelected] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchDevicesForSolution = async () => {
      if (!solutionId) {
        setIsLoading(false);
        setAvailableDevices([]);
        return;
      }
      setIsLoading(true);
      try {
        const devices =
          await deviceSolutionService.getDevicesBySolution(solutionId);
        console.log("Fetched devices:", devices);
        setAvailableDevices(
          devices.map((d) => ({
            device_id: d.device_id,
            device_name: d.device_name,
            device_location: d.device_location,
          }))
        );
        if (!initialSelectedDevices) {
          setSelectedDevices(devices.map((d) => d.device_id));
        }
      } catch (error) {
        console.error("Failed to fetch devices for solution:", error);
        setAvailableDevices([]);
        // Handle error appropriately in UI if needed, e.g., toast notification
      } finally {
        setIsLoading(false);
      }
    };
    fetchDevicesForSolution();
  }, [solutionId, initialSelectedDevices]);

  useEffect(() => {
    if (availableDevices.length > 0) {
      setIsAllSelected(selectedDevices.length === availableDevices.length);
    } else {
      setIsAllSelected(false);
    }
    if (onSelectionChange) {
      onSelectionChange(selectedDevices);
    }
  }, [selectedDevices, availableDevices, onSelectionChange]);

  const handleDeviceToggle = (deviceId: string) => {
    setSelectedDevices((prevSelected) =>
      prevSelected.includes(deviceId)
        ? prevSelected.filter((d) => d !== deviceId)
        : [...prevSelected, deviceId]
    );
  };

  const handleSelectAllToggle = () => {
    if (isAllSelected) {
      setSelectedDevices([]);
    } else {
      setSelectedDevices(availableDevices.map((d) => d.device_id));
    }
  };

  if (isLoading) {
    return (
      <FilterCard title="デバイス">
        <div className="text-sm text-gray-500">デバイスを読み込み中...</div>
      </FilterCard>
    );
  }

  if (availableDevices.length === 0) {
    return (
      <FilterCard title="デバイス">
        <div className="text-sm text-gray-500">
          利用可能なデバイスがありません。
        </div>
      </FilterCard>
    );
  }

  return (
    <FilterCard title="デバイス">
      <div className="space-y-2">
        <div className="flex items-center space-x-2">
          <Checkbox
            id="select-all-devices"
            checked={isAllSelected}
            onCheckedChange={handleSelectAllToggle}
            disabled={availableDevices.length === 0}
          />
          <Label htmlFor="select-all-devices" className="text-sm font-medium">
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
                  id={device.device_id}
                  checked={selectedDevices.includes(device.device_id)}
                  onCheckedChange={() => handleDeviceToggle(device.device_id)}
                />
                <Label
                  htmlFor={device.device_id}
                  className="text-sm font-normal"
                >
                  {device.device_location + "_" + device.device_name}
                </Label>
              </div>
            ))}
          </div>
        </ScrollArea>
      </div>
    </FilterCard>
  );
}
