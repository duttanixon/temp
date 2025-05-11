// src/app/(main)/devices/_components/DeviceCreateForm.tsx
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
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
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Initialize form data
  const [formData, setFormData] = useState({
    customer_id: "", // Optional - can be empty
    device_type: "",
    description: "",
    mac_address: "",
    serial_number: "",
    firmware_version: "",
    location: "",
    ip_address: "",
  });

  const handleChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement
    >
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      // Basic validation - only device_type is required
      if (!formData.device_type) {
        throw new Error("デバイスタイプを選択してください");
      }

      const response = await fetch(`/api/devices`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "デバイスの作成に失敗しました");
      }

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
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-white rounded-lg border border-[#BDC3C7] overflow-hidden">
      <div className="px-6 py-4 border-b border-[#BDC3C7]">
        <h2 className="text-lg font-semibold text-[#2C3E50]">
          新規デバイス情報
        </h2>
      </div>

      <form onSubmit={handleSubmit} className="p-6 space-y-6">
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
              name="customer_id"
              value={formData.customer_id}
              onChange={handleChange}
              className="mt-1 block w-full rounded-md border border-[#BDC3C7] px-3 py-2"
            >
              <option value="">顧客を選択（任意）</option>
              {customers.map((customer) => (
                <option key={customer.customer_id} value={customer.customer_id}>
                  {customer.name}
                </option>
              ))}
            </select>
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
              name="device_type"
              value={formData.device_type}
              onChange={handleChange}
              className="mt-1 block w-full rounded-md border border-[#BDC3C7] px-3 py-2"
              required
            >
              <option value="">選択してください</option>
              <option value="NVIDIA_JETSON">NVIDIA Jetson</option>
              <option value="RASPBERRY_PI">Raspberry Pi</option>
            </select>
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
              name="mac_address"
              value={formData.mac_address}
              onChange={handleChange}
              className="mt-1 block w-full rounded-md border border-[#BDC3C7] px-3 py-2"
              placeholder="例: 00:11:22:33:44:55"
            />
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
              name="serial_number"
              value={formData.serial_number}
              onChange={handleChange}
              className="mt-1 block w-full rounded-md border border-[#BDC3C7] px-3 py-2"
            />
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
              name="firmware_version"
              value={formData.firmware_version}
              onChange={handleChange}
              className="mt-1 block w-full rounded-md border border-[#BDC3C7] px-3 py-2"
            />
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
              name="location"
              value={formData.location}
              onChange={handleChange}
              className="mt-1 block w-full rounded-md border border-[#BDC3C7] px-3 py-2"
            />
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
              name="ip_address"
              value={formData.ip_address}
              onChange={handleChange}
              className="mt-1 block w-full rounded-md border border-[#BDC3C7] px-3 py-2"
              placeholder="例: 192.168.1.100"
            />
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
              name="description"
              value={formData.description}
              onChange={handleChange}
              rows={3}
              className="mt-1 block w-full rounded-md border border-[#BDC3C7] px-3 py-2"
              placeholder="デバイスの説明や用途を入力してください"
            />
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
