"use client";

import { FormField } from "@/components/forms/FormField";
import {
  DeviceUpdateFormValues,
  deviceUpdateSchema,
} from "@/schemas/deviceSchemas";
import { deviceService } from "@/services/deviceService";
import { Device } from "@/types/device";
import { isDeviceProvisioned } from "@/utils/devices/deviceHelpers";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

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
          <FormField
            id="description"
            label="説明"
            type="text"
            register={register}
            errors={errors}
            as="textarea"
            rows={3}
            placeholder="デバイスの説明や用途などを入力してください"
          />

          <FormField
            id="location"
            label="設置場所"
            type="text"
            register={register}
            errors={errors}
          />

          <FormField
            id="firmware_version"
            label="ファームウェアバージョン"
            type="text"
            register={register}
            errors={errors}
          />

          {/* IP Address field - only if it was in the original device data */}
          {device.ip_address !== undefined && (
            <FormField
              id="ip_address"
              label="IPアドレス"
              type="text"
              register={register}
              errors={errors}
            />
          )}
        </div>

        <div className="flex justify-end space-x-4">
          <button
            type="button"
            onClick={() => router.back()}
            className="px-4 py-2 border border-[#BDC3C7] rounded-md text-sm text-[#7F8C8D] hover:bg-[#ECF0F1]"
            disabled={isSubmitting}>
            キャンセル
          </button>
          <button
            type="submit"
            className="px-4 py-2 bg-[#27AE60] text-white rounded-md text-sm hover:bg-[#219955]"
            disabled={isSubmitting}>
            {isSubmitting ? "更新中..." : "保存"}
          </button>
        </div>
      </form>
    </div>
  );
}
