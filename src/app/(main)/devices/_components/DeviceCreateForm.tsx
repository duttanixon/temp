"use client";

import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { deviceService } from "@/services/deviceService";
import { DeviceCreateFormValues, deviceCreateSchema } from "@/schemas/deviceSchemas";

type Customer = {
  customer_id: string;
  name: string;
};

type DeviceCreateFormProps = {
  customers: Customer[];
};

export default function DeviceCreateForm({ customers }: DeviceCreateFormProps) {
  const router = useRouter();

  // Initialize React Hook Form with Zod validation
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<DeviceCreateFormValues>({
    resolver: zodResolver(deviceCreateSchema),
    defaultValues: {
      customer_id: "",
      device_type: undefined, // Let the user select
      description: "",
      mac_address: "",
      serial_number: "",
      firmware_version: "",
      location: "",
      ip_address: "",
    },
  });

  const onSubmit = async (data: DeviceCreateFormValues) => {
    try {
      // Use the service to create the device
      await deviceService.createDevice(data);

      toast.success("デバイスが作成されました", {
        description: "新しいデバイスが正常に作成されました。",
      });

      // Redirect to the device list page
      router.push("/devices");
      router.refresh();
    } catch (error) {
      console.error("Error creating device:", error);
      toast.error("作成エラー", {
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
          新規デバイス情報
        </h2>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Customer Selection - Optional */}
          <div>
            <label
              htmlFor="customer_id"
              className="block text-sm font-medium text-[#7F8C8D]"
            >
              顧客
            </label>
            <select
              id="customer_id"
              {...register("customer_id")}
              className="mt-1 block w-full rounded-md border border-[#BDC3C7] px-3 py-2"
            >
              <option value="">顧客を選択（任意）</option>
              {customers.map((customer) => (
                <option key={customer.customer_id} value={customer.customer_id}>
                  {customer.name}
                </option>
              ))}
            </select>
            {errors.customer_id && (
              <p className="mt-1 text-xs text-red-500">{errors.customer_id.message}</p>
            )}
            <p className="mt-1 text-xs text-[#7F8C8D]">
              顧客を選択しない場合、後で割り当てることができます
            </p>
          </div>

          {/* Device Type Selection */}
          <div>
            <label
              htmlFor="device_type"
              className="block text-sm font-medium text-[#7F8C8D]"
            >
              デバイスタイプ <span className="text-red-500">*</span>
            </label>
            <select
              id="device_type"
              {...register("device_type")}
              className="mt-1 block w-full rounded-md border border-[#BDC3C7] px-3 py-2"
            >
              <option value="">選択してください</option>
              <option value="NVIDIA_JETSON">NVIDIA Jetson</option>
              <option value="RASPBERRY_PI">Raspberry Pi</option>
            </select>
            {errors.device_type && (
              <p className="mt-1 text-xs text-red-500">{errors.device_type.message}</p>
            )}
          </div>

          {/* MAC Address */}
          <div>
            <label
              htmlFor="mac_address"
              className="block text-sm font-medium text-[#7F8C8D]"
            >
              MACアドレス
            </label>
            <input
              type="text"
              id="mac_address"
              {...register("mac_address")}
              className="mt-1 block w-full rounded-md border border-[#BDC3C7] px-3 py-2"
              placeholder="例: 00:11:22:33:44:55"
            />
            {errors.mac_address && (
              <p className="mt-1 text-xs text-red-500">{errors.mac_address.message}</p>
            )}
          </div>

          {/* Serial Number */}
          <div>
            <label
              htmlFor="serial_number"
              className="block text-sm font-medium text-[#7F8C8D]"
            >
              シリアル番号
            </label>
            <input
              type="text"
              id="serial_number"
              {...register("serial_number")}
              className="mt-1 block w-full rounded-md border border-[#BDC3C7] px-3 py-2"
            />
            {errors.serial_number && (
              <p className="mt-1 text-xs text-red-500">{errors.serial_number.message}</p>
            )}
          </div>

          {/* Firmware Version */}
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

          {/* Location */}
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

          {/* IP Address */}
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
              placeholder="例: 192.168.1.100"
            />
            {errors.ip_address && (
              <p className="mt-1 text-xs text-red-500">{errors.ip_address.message}</p>
            )}
          </div>

          {/* Description - Full Width */}
          <div className="md:col-span-2">
            <label
              htmlFor="description"
              className="block text-sm font-medium text-[#7F8C8D]"
            >
              説明
            </label>
            <textarea
              id="description"
              {...register("description")}
              rows={3}
              className="mt-1 block w-full rounded-md border border-[#BDC3C7] px-3 py-2"
              placeholder="デバイスの説明や用途を入力してください"
            />
            {errors.description && (
              <p className="mt-1 text-xs text-red-500">{errors.description.message}</p>
            )}
          </div>
        </div>

        <div className="flex justify-end space-x-4">
          <button
            type="button"
            onClick={() => router.push("/devices")}
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
            {isSubmitting ? "作成中..." : "作成"}
          </button>
        </div>
      </form>
    </div>
  );
}