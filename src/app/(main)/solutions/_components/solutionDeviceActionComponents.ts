import { Device } from "@/types/device";
import { Solution } from "@/types/solution";
import { FC } from "react";
import CityEyeDeviceActions from "../[solutionId]/actions/[deviceId]/_components/DeviceActions";
// import DefaultDeviceActions from './DefaultDeviceActions';

type SolutionDeviceActionProps = {
  device: Device;
  solution: Solution;
};

export const solutionDeviceActionComponents: Record<
  string,
  FC<SolutionDeviceActionProps>
> = {
  cityeye: CityEyeDeviceActions,
  //   default: DefaultDeviceActions,
};
