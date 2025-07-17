import { deviceService } from "@/services/deviceService";
import { Device } from "@/types/device";
import { useEffect, useState } from "react";

type useGetDeviceProps = {
  id: string;
};
export const useGetDevice = ({ id }: useGetDeviceProps) => {
  const [device, setDevice] = useState<Device[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setIsLoading(true);
    deviceService
      .getDevice(id)
      .then((data) => {
        if (data) {
          setDevice([data]);
        } else {
          setError("デバイスが見つかりません");
        }
      })
      .catch((error) => {
        setError(error.message ?? "顧客情報の取得に失敗しました");
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [id]);

  return { device, isLoading, error };
};
