import { Device } from "@/types/device";
import DeviceStatusBadge from "./DeviceStatusBadge";

type DeviceInfoCardProps = {
  device: Device;
};

export default function DeviceInfoCard({ device }: DeviceInfoCardProps) {
  return (
    <div className="bg-white rounded-lg border border-[#BDC3C7] overflow-hidden">
      <div className="px-6 py-4 border-b border-[#BDC3C7]">
        <h2 className="text-lg font-semibold text-[#2C3E50]">デバイス情報</h2>
      </div>

      <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Left column - Key device information */}
        <div className="space-y-4">
          <div className="flex justify-between">
            <span className="text-sm text-[#7F8C8D]">ソリューション名</span>
            <span className="text-sm font-medium text-[#2C3E50]">
              -
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-[#7F8C8D]">デバイスタイプ</span>
            <span className="text-sm font-medium text-[#2C3E50]">
              {device.device_type}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-[#7F8C8D]">ステータス</span>
            <span className="text-sm font-medium text-[#2C3E50]">
              <DeviceStatusBadge status={device.status} isOnline={device.is_online} />
            </span>
          </div>
        </div>

        {/* Right column - Additional device information */}
        <div className="space-y-4">
          <div className="flex justify-between">
            <span className="text-sm text-[#7F8C8D]">IPアドレス</span>
            <span className="text-sm font-medium text-[#2C3E50]">
              {device.ip_address || "-"}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-[#7F8C8D]">最終接続</span>
            <span className="text-sm font-medium text-[#2C3E50]">
              {device.last_connected
                ? new Date(device.last_connected).toLocaleString()
                : "-"}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-[#7F8C8D]">顧客名</span>
            <span className="text-sm font-medium text-[#2C3E50]">
              {device.customer_name || "-"}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}