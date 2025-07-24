import { Device } from "@/types/device";
import { Solution } from "@/types/solution";
import { FC } from "react";
import CityEyeDeviceActions from "../[solutionId]/[deviceId]/_components/DeviceActions";
// import DefaultDeviceActions from './DefaultDeviceActions';

type DeviceActionProps = {
  device: Device;
  solution: Solution;
};

export const deviceActionComponents: Record<string, FC<DeviceActionProps>> = {
  cityeye: CityEyeDeviceActions,
  //   default: DefaultDeviceActions,
};
