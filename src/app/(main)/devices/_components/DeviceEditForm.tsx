"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

type DeviceEditFormProps = {
  device: any;
};

export default function DeviceEditForm({ device }: DeviceEditFormProps) {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Initialize form with current device values
  const [formData, setFormData] = useState({
    description: device.description || "",
    location: device.location || "",
    firmware_version: device.firmware_version || "",
    // Only include IP address if user is Admin/Engineer (based on existing device data)
    ...(device.ip_address !== undefined && {
      ip_address: device.ip_address || "",
    }),
  });

  // Determine if device is provisioned to handle field restrictions
  const isProvisioned = [
    "PROVISIONED",
    "ACTIVE",
    "MAINTENANCE",
    "DECOMMISSIONED",
  ].includes(device.status);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const response = await fetch(`/api/devices/${device.device_id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "デバイスの更新に失敗しました");
      }

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
    } finally {
      setIsSubmitting(false);
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

      <form onSubmit={handleSubmit} className="p-6 space-y-6">
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
              name="description"
              value={formData.description}
              onChange={handleChange}
              className="mt-1 block w-full rounded-md border border-[#BDC3C7] px-3 py-2"
              rows={3}
            />
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
              name="location"
              value={formData.location}
              onChange={handleChange}
              className="mt-1 block w-full rounded-md border border-[#BDC3C7] px-3 py-2"
            />
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
              name="firmware_version"
              value={formData.firmware_version}
              onChange={handleChange}
              className="mt-1 block w-full rounded-md border border-[#BDC3C7] px-3 py-2"
            />
          </div>

          {/* IP Address field - only for Admin/Engineer roles */}
          {formData.ip_address !== undefined && (
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
              />
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
