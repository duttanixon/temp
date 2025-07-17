"use client";

import { type FC } from "react";
import { useRouter } from "next/navigation";
import { Edit, Video } from "lucide-react";
import { TbPolygon } from "react-icons/tb";
import { Device } from "@/types/device";

type CityEyeDeviceActionsProps = {
  device: Device;
};

const CityEyeDeviceActions: FC<CityEyeDeviceActionsProps> = ({ device }) => {
  const router = useRouter();

  const handleEdit = (e: React.MouseEvent) => {
    e.stopPropagation();
    // This will now navigate to a "city_eye" specific edit page.
    // router.push(`/analytics/cityeye/edit/${device.device_id}`);
    router.push(`/devices/cityeye/${device.device_id}/edit`);
  };

  const handlePolygonSettings = (e: React.MouseEvent) => {
    e.stopPropagation();
    router.push(`/devices/cityeye/${device.device_id}/polygon-settings`);
  };

  const handleLiveStream = (e: React.MouseEvent) => {
    e.stopPropagation();
    router.push(`/devices/cityeye/${device.device_id}/live`);
  };

  return (
    <div className="flex size-full items-center justify-center gap-4">
      <button
        onClick={handleEdit}
        className="group flex size-[34px] items-center justify-center rounded-full transition-colors duration-300 hover:bg-[#3498DB]"
      >
        <Edit className="text-xl text-[#7F8C8D] transition-colors duration-300 group-hover:text-white" />
      </button>
      <button
        onClick={handlePolygonSettings}
        className="group flex size-[34px] items-center justify-center rounded-full transition-colors duration-300 hover:bg-[#3498DB]"
        title="ポリゴン設定"
      >
        <TbPolygon className="text-xl text-[#7F8C8D] transition-colors duration-300 group-hover:text-white" />
      </button>
      <button
        onClick={handleLiveStream}
        className="group flex size-[34px] items-center justify-center rounded-full transition-colors duration-300 hover:bg-[#E74C3C]"
        title="ライブストリーム"
      >
        <Video className="text-xl text-[#7F8C8D] transition-colors duration-300 group-hover:text-white" />
      </button>
    </div>
  );
};

export default CityEyeDeviceActions;
