// src/app/(main)/analytics/cityeye/_components/filters/DevicesFilter.tsx
"use client";

import React, { useState, useEffect } from "react";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { FilterCard } from "./FilterCard";
import { ScrollArea } from "@/components/ui/scroll-area";
import { deviceService } from "@/services/deviceService"; // Assuming you have this service
import { Device } from "@/types/device"; // Assuming you have this type

interface DevicesFilterProps {
  initialSelectedDevices?: string[];
  onSelectionChange?: (selectedDevices: string[]) => void;
  // customerId and solutionId might be needed to fetch relevant devices
  customerId?: string;
  solutionId?: string;
}

export function DevicesFilter({
  initialSelectedDevices,
  onSelectionChange,
  customerId,
  solutionId,
}: DevicesFilterProps) {
  const [availableDevices, setAvailableDevices] = useState<Device[]>([]);
  const [selectedDevices, setSelectedDevices] = useState<string[]>(initialSelectedDevices || []);
  const [isAllSelected, setIsAllSelected] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Fetch devices (this is a placeholder, implement actual fetching logic)
    const fetchDevices = async () => {
      setIsLoading(true);
      try {
        // Replace with your actual API call
        // Example: const devices = await deviceService.getDevicesForCustomerSolution(customerId, solutionId);
        // For now, using placeholder data
        const mockDevices: Device[] = [
          { device_id: "device1", name: "Camera 101", device_type: "NVIDIA_JETSON", status: "ACTIVE", is_online: true, customer_id: "cust1", created_at: new Date().toISOString() },
          { device_id: "device2", name: "Sensor Alpha", device_type: "RASPBERRY_PI", status: "ACTIVE", is_online: false, customer_id: "cust1", created_at: new Date().toISOString() },
          { device_id: "device3", name: "Gateway 7", device_type: "NVIDIA_JETSON", status: "INACTIVE", is_online: true, customer_id: "cust1", created_at: new Date().toISOString() },
        ];
        setAvailableDevices(mockDevices);
        if (!initialSelectedDevices) {
          setSelectedDevices(mockDevices.map(d => d.device_id));
        }
      } catch (error) {
        console.error("Failed to fetch devices:", error);
        // Handle error appropriately
      } finally {
        setIsLoading(false);
      }
    };
    fetchDevices();
  }, [customerId, solutionId, initialSelectedDevices]);

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
      setSelectedDevices(availableDevices.map(d => d.device_id));
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
        <div className="text-sm text-gray-500">利用可能なデバイスがありません。</div>
      </FilterCard>
    )
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
              <div key={device.device_id} className="flex items-center space-x-2">
                <Checkbox
                  id={device.device_id}
                  checked={selectedDevices.includes(device.device_id)}
                  onCheckedChange={() => handleDeviceToggle(device.device_id)}
                />
                <Label htmlFor={device.device_id} className="text-sm font-normal">
                  {device.name}
                </Label>
              </div>
            ))}
          </div>
        </ScrollArea>
      </div>
    </FilterCard>
  );
}