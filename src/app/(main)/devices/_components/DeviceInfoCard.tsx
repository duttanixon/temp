import { formatDistanceToNow } from "date-fns";
import { ja } from "date-fns/locale";

type DeviceInfoCardProps = {
  device: any;
};

export default function DeviceInfoCard({ device }: DeviceInfoCardProps) {
  const getStatusBadge = (status: string, isOnline: boolean) => {
    let bgColor = "bg-gray-500";

    if (isOnline) {
      bgColor = "bg-green-500";
    } else {
      switch (status) {
        case "ACTIVE":
          bgColor = "bg-blue-500";
          break;
        case "PROVISIONED":
          bgColor = "bg-yellow-500";
          break;
        case "INACTIVE":
          bgColor = "bg-gray-500";
          break;
        case "MAINTENANCE":
          bgColor = "bg-orange-500";
          break;
        case "DECOMMISSIONED":
          bgColor = "bg-red-500";
          break;
      }
    }

    return (
      <span className="inline-flex items-center">
        <span className={`h-2.5 w-2.5 rounded-full ${bgColor} mr-2`}></span>
        <span>{status}</span>
        {isOnline && <span className="ml-2 text-green-600">(オンライン)</span>}
      </span>
    );
  };

  return (
    <div className="bg-white rounded-lg border border-[#BDC3C7] overflow-hidden">
      <div className="px-6 py-4 border-b border-[#BDC3C7]">
        <h2 className="text-lg font-semibold text-[#2C3E50]">デバイス情報</h2>
      </div>

      <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-4">
          <div>
            <h3 className="text-sm font-medium text-[#7F8C8D]">基本情報</h3>
            <div className="mt-2 space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-[#7F8C8D]">デバイス名</span>
                <span className="text-sm font-medium text-[#2C3E50]">
                  {device.name}
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
                  {getStatusBadge(device.status, device.is_online)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-[#7F8C8D]">MACアドレス</span>
                <span className="text-sm font-medium text-[#2C3E50]">
                  {device.mac_address || "-"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-[#7F8C8D]">シリアル番号</span>
                <span className="text-sm font-medium text-[#2C3E50]">
                  {device.serial_number || "-"}
                </span>
              </div>
            </div>
          </div>

          <div>
            <h3 className="text-sm font-medium text-[#7F8C8D]">
              プロビジョン情報
            </h3>
            <div className="mt-2 space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-[#7F8C8D]">Thing Name</span>
                <span className="text-sm font-medium text-[#2C3E50]">
                  {device.thing_name || "-"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-[#7F8C8D]">最終接続</span>
                <span className="text-sm font-medium text-[#2C3E50]">
                  {device.last_connected
                    ? formatDistanceToNow(new Date(device.last_connected), {
                        addSuffix: true,
                        locale: ja,
                      })
                    : "-"}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <h3 className="text-sm font-medium text-[#7F8C8D]">その他の情報</h3>
            <div className="mt-2 space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-[#7F8C8D]">説明</span>
                <span className="text-sm font-medium text-[#2C3E50]">
                  {device.description || "-"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-[#7F8C8D]">
                  ファームウェアバージョン
                </span>
                <span className="text-sm font-medium text-[#2C3E50]">
                  {device.firmware_version || "-"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-[#7F8C8D]">IPアドレス</span>
                <span className="text-sm font-medium text-[#2C3E50]">
                  {device.ip_address || "-"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-[#7F8C8D]">場所</span>
                <span className="text-sm font-medium text-[#2C3E50]">
                  {device.location || "-"}
                </span>
              </div>
            </div>
          </div>

          <div>
            <h3 className="text-sm font-medium text-[#7F8C8D]">登録情報</h3>
            <div className="mt-2 space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-[#7F8C8D]">作成日</span>
                <span className="text-sm font-medium text-[#2C3E50]">
                  {new Date(device.created_at).toLocaleDateString("ja-JP")}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-[#7F8C8D]">最終更新</span>
                <span className="text-sm font-medium text-[#2C3E50]">
                  {device.updated_at
                    ? new Date(device.updated_at).toLocaleDateString("ja-JP")
                    : "-"}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
