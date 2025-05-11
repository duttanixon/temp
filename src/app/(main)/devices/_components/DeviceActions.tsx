"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

type DeviceActionsProps = {
  device: any;
};

export default function DeviceActions({ device }: DeviceActionsProps) {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);

  // Determine which actions are available based on device status
  const canProvision = device.status === "CREATED";
  const canActivate =
    device.status === "PROVISIONED" || device.status === "INACTIVE";
  const canDecommission = device.status !== "DECOMMISSIONED";

  const executeAction = async (action: string, displayName: string) => {
    setIsLoading(true);

    try {
      const url = `/api/devices/${device.device_id}/${action}`;
      console.log(`Sending request to: ${url}`);

      const response = await fetch(
        `/api/devices/${device.device_id}/${action}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        console.error(`API error (${response.status}):`, errorData);
        throw new Error(errorData.detail || `${displayName}に失敗しました`);
      }

      const data = await response.json();
      console.log(`${action} response:`, data);

      toast.success(`${displayName}が完了しました`, {
        description: `デバイス ${device.name} の${displayName}が正常に完了しました。`,
      });

      // Refresh the page to show updated device status
      router.refresh();
    } catch (error) {
      console.error(`Error during ${action}:`, error);
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
  const handleActivate = () => executeAction("activate", "アクティベーション");
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

      {canActivate && (
        <button
          onClick={handleActivate}
          disabled={isLoading}
          className="bg-green-600 text-white px-4 py-2 rounded-md text-sm hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50"
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
