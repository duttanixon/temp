import { FC } from 'react';
import { Device } from '@/types/device';
import CityEyeDeviceActions from '../cityeye/_components/DeviceActions';
// import DefaultDeviceActions from './DefaultDeviceActions';

type DeviceActionProps = {
    device: Device;
}

export const deviceActionComponents: Record<string, FC<DeviceActionProps>> = {
  cityeye: CityEyeDeviceActions,
//   default: DefaultDeviceActions,
};