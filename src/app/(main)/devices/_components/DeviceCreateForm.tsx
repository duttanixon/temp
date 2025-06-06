"use client";

import { FormField } from "@/components/forms/FormField";
import {
  DeviceCreateFormValues,
  deviceCreateSchema,
} from "@/schemas/deviceSchemas";
import { deviceService } from "@/services/deviceService";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

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
      console.log("Error creating device:", error);
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
              className="block text-sm font-medium text-[#7F8C8D]">
              顧客
            </label>
            <select
              id="customer_id"
              {...register("customer_id")}
              className="mt-1 block w-full rounded-md border border-[#BDC3C7] px-3 py-2">
              <option value="">顧客を選択（任意）</option>
              {customers.map((customer) => (
                <option key={customer.customer_id} value={customer.customer_id}>
                  {customer.name}
                </option>
              ))}
            </select>
            {errors.customer_id && (
              <p className="mt-1 text-xs text-red-500">
                {errors.customer_id.message}
              </p>
            )}
            <p className="mt-1 text-xs text-[#7F8C8D]">
              顧客を選択しない場合、後で割り当てることができます
            </p>
          </div>

          {/* Device Type Selection */}
          <div>
            <label
              htmlFor="device_type"
              className="block text-sm font-medium text-[#7F8C8D]">
              デバイスタイプ <span className="text-red-500">*</span>
            </label>
            <select
              id="device_type"
              {...register("device_type")}
              className="mt-1 block w-full rounded-md border border-[#BDC3C7] px-3 py-2">
              <option value="">選択してください</option>
              <option value="NVIDIA_JETSON">NVIDIA Jetson</option>
              <option value="RASPBERRY_PI">Raspberry Pi</option>
            </select>
            {errors.device_type && (
              <p className="mt-1 text-xs text-red-500">
                {errors.device_type.message}
              </p>
            )}
          </div>

          {/* Replace repetitive form fields with our FormField component */}
          <FormField
            id="mac_address"
            label="MACアドレス"
            type="text"
            register={register}
            errors={errors}
            placeholder="例: 00:11:22:33:44:55"
          />

          <FormField
            id="serial_number"
            label="シリアル番号"
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

          <FormField
            id="location"
            label="設置場所"
            type="text"
            register={register}
            errors={errors}
          />

          <FormField
            id="ip_address"
            label="IPアドレス"
            type="text"
            register={register}
            errors={errors}
            placeholder="例: 192.168.1.100"
          />

          {/* Description - Full Width */}
          <div className="md:col-span-2">
            <FormField
              id="description"
              label="説明"
              type="text"
              register={register}
              errors={errors}
              as="textarea"
              rows={3}
              placeholder="デバイスの説明や用途を入力してください"
            />
          </div>
        </div>

        <div className="flex justify-end space-x-4">
          <button
            type="button"
            onClick={() => router.push("/devices")}
            className="px-4 py-2 border border-[#BDC3C7] rounded-md text-sm text-[#7F8C8D] hover:bg-[#ECF0F1]"
            disabled={isSubmitting}>
            キャンセル
          </button>
          <button
            type="submit"
            className="px-4 py-2 bg-[#27AE60] text-white rounded-md text-sm hover:bg-[#219955]"
            disabled={isSubmitting}>
            {isSubmitting ? "作成中..." : "作成"}
          </button>
        </div>
      </form>
    </div>
  );
}
