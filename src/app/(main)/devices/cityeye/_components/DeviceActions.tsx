"use client";

import { type FC } from "react";
import { useRouter } from "next/navigation";
import { Edit } from "lucide-react";
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
        router.push(`/devices/detail/later/edit?deviceId=${device.device_id}`);
      };

      return (
        <div className="flex size-full items-center justify-center">
            <button
              onClick={handleEdit}
              className="group flex size-[30px] items-center justify-center rounded-full transition-colors duration-300 hover:bg-[#27AE60]"
            >
              <Edit className="text-xl text-[#7F8C8D] transition-colors duration-300 group-hover:text-white" />
            </button>
        </div>
      );
    };
    
    export default CityEyeDeviceActions;