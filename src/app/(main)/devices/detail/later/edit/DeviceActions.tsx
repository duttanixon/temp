"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Device } from "@/types/device";
import { deviceService } from "@/services/deviceService"; 
import { 
  canProvisionDevice, 
  canReprovisionDevice, 
  canDecommissionDevice 
} from "@/utils/devices/deviceHelpers";

type DeviceActionsProps = {
  device: Device;
};

export default function DeviceActions({ device }: DeviceActionsProps) {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);

  // Determine which actions are available based on device status
  const canProvision = canProvisionDevice(device);
  const canReprovision = canReprovisionDevice(device);
  const canDecommission = canDecommissionDevice(device);

  const executeAction = async (action: string, displayName: string) => {
    setIsLoading(true);

    try {
      const updatedDevice = await deviceService.executeDeviceAction(device.device_id, action);   
      
      // Update the local state with the updated device
      // setCurrentDevice(updatedDevice);
      

      toast.success(`${displayName}が完了しました`, {
        description: `デバイス ${device.name} の${displayName}が正常に完了しました。`,
      });

      // Refresh the page to show updated device status
      router.refresh();
    } catch (error) {
      console.log(`Error during ${action}:`, error);
      toast.error(`${displayName}エラー`, {
        description:
          error instanceof Error
            ? error.message
            : "予期せぬエラーが発生しました",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleProvision = () => executeAction("provision", "プロビジョン");
  const handleReprovision = () => executeAction("activate", "再プロビジョン");
  const handleDecommission = () => executeAction("decommission", "廃止");

  return (
    <div className="flex items-center space-x-4">
      {canProvision && (
        <button
          onClick={handleProvision}
          disabled={isLoading}
          className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
        >
          プロビジョン
        </button>
      )}

      {canReprovision && (
        <button
          onClick={handleReprovision}
          disabled={isLoading}
          className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
        >
          アクティベート
        </button>
      )}

      {canDecommission && (
        <button
          onClick={handleDecommission}
          disabled={isLoading}
          className="bg-red-600 text-white px-4 py-2 rounded-md text-sm hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-50"
        >
          廃止
        </button>
      )}

      <button
        onClick={() => router.push(`/devices/${device.device_id}/edit`)}
        disabled={isLoading}
        className="bg-gray-100 text-gray-700 px-4 py-2 rounded-md text-sm hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50"
      >
        編集
      </button>
    </div>
  );
}
