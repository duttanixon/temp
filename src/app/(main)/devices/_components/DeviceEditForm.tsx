"use client";

import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Device } from "@/types/device";
import { deviceService } from "@/services/deviceService";
import { DeviceUpdateFormValues, deviceUpdateSchema } from "@/schemas/deviceSchemas";
import { isDeviceProvisioned } from "@/utils/devices/deviceHelpers";

type DeviceEditFormProps = {
  device: Device;
};

export default function DeviceEditForm({ device }: DeviceEditFormProps) {
  const router = useRouter();

  // Determine if device is provisioned to handle field restrictions
  const isProvisioned = isDeviceProvisioned(device);

  // Initialize React Hook Form with Zod validation
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<DeviceUpdateFormValues>({
    resolver: zodResolver(deviceUpdateSchema),
    defaultValues: {
      description: device.description || "",
      location: device.location || "",
      firmware_version: device.firmware_version || "",
      ip_address: device.ip_address || "",
    },
  });

  const onSubmit = async (data: DeviceUpdateFormValues) => {
    try {
      await deviceService.updateDevice(device.device_id, data);
      
      toast.success("デバイスが更新されました", {
        description: `デバイス「${device.name}」の情報が正常に更新されました。`,
      });
      
      // Redirect back to device details page
      router.push(`/devices/${device.device_id}`);
      router.refresh();
    } catch (error) {
      console.error("Error updating device:", error);
      toast.error("更新エラー", {
        description:
          error instanceof Error
            ? error.message
            : "予期せぬエラーが発生しました",
      });
    }
  };

  return (
    <div className="bg-white rounded-lg border border-[#BDC3C7] overflow-hidden">
      <div className="px-6 py-4 border-b border-[#BDC3C7]">
        <h2 className="text-lg font-semibold text-[#2C3E50]">
          デバイス情報を編集
        </h2>
        {isProvisioned && (
          <p className="mt-1 text-sm text-amber-600">
            注意: プロビジョン済みのデバイスは一部の情報のみ編集可能です
          </p>
        )}
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-6">
        <div className="grid grid-cols-1 gap-6">
          <div>
            <label
              htmlFor="description"
              className="block text-sm font-medium text-[#7F8C8D]"
            >
              説明
            </label>
            <textarea
              id="description"
              {...register("description")}
              className="mt-1 block w-full rounded-md border border-[#BDC3C7] px-3 py-2"
              rows={3}
            />
            {errors.description && (
              <p className="mt-1 text-xs text-red-500">{errors.description.message}</p>
            )}
            <p className="mt-1 text-xs text-[#7F8C8D]">
              デバイスの説明や用途などを入力してください
            </p>
          </div>

          <div>
            <label
              htmlFor="location"
              className="block text-sm font-medium text-[#7F8C8D]"
            >
              設置場所
            </label>
            <input
              type="text"
              id="location"
              {...register("location")}
              className="mt-1 block w-full rounded-md border border-[#BDC3C7] px-3 py-2"
            />
            {errors.location && (
              <p className="mt-1 text-xs text-red-500">{errors.location.message}</p>
            )}
          </div>

          <div>
            <label
              htmlFor="firmware_version"
              className="block text-sm font-medium text-[#7F8C8D]"
            >
              ファームウェアバージョン
            </label>
            <input
              type="text"
              id="firmware_version"
              {...register("firmware_version")}
              className="mt-1 block w-full rounded-md border border-[#BDC3C7] px-3 py-2"
            />
            {errors.firmware_version && (
              <p className="mt-1 text-xs text-red-500">{errors.firmware_version.message}</p>
            )}
          </div>

          {/* IP Address field - only if it was in the original device data */}
          {device.ip_address !== undefined && (
            <div>
              <label
                htmlFor="ip_address"
                className="block text-sm font-medium text-[#7F8C8D]"
              >
                IPアドレス
              </label>
              <input
                type="text"
                id="ip_address"
                {...register("ip_address")}
                className="mt-1 block w-full rounded-md border border-[#BDC3C7] px-3 py-2"
              />
              {errors.ip_address && (
                <p className="mt-1 text-xs text-red-500">{errors.ip_address.message}</p>
              )}
            </div>
          )}
        </div>

        <div className="flex justify-end space-x-4">
          <button
            type="button"
            onClick={() => router.back()}
            className="px-4 py-2 border border-[#BDC3C7] rounded-md text-sm text-[#7F8C8D] hover:bg-[#ECF0F1]"
            disabled={isSubmitting}
          >
            キャンセル
          </button>
          <button
            type="submit"
            className="px-4 py-2 bg-[#27AE60] text-white rounded-md text-sm hover:bg-[#219955]"
            disabled={isSubmitting}
          >
            {isSubmitting ? "更新中..." : "保存"}
          </button>
        </div>
      </form>
    </div>
  );
}