import { Device, DeviceStatus } from '@/types/device';

/**
 * Determines if a device can be provisioned based on its current status
 */
export function canProvisionDevice(device: Device): boolean {
    return device.status === 'CREATED';
  }

/**
 * Determines if a device can be decommissioned based on its current status
 * (PROVISIONED devices can be decommissioned)
 */
export function canDecommissionDevice(device: Device): boolean {
  return device.status === 'PROVISIONED' || device.status === 'ACTIVE';
}


/**
 * Determines if a device can be re-provisioned after being decommissioned
 */
export function canReprovisionDevice(device: Device): boolean {
  return device.status === 'DECOMMISSIONED';
}
  

/**
 * Returns the appropriate CSS class for the status indicator based on device online status
 */
export function getStatusColor(status: DeviceStatus, isOnline: boolean): string {
  return isOnline ? "bg-green-500" : "bg-gray-500";
}

  
/**
 * Determines if a device is provisioned and has limited editable fields
 */
export function isDeviceProvisioned(device: Device): boolean {
    return [
      'PROVISIONED',
      'ACTIVE',
      'MAINTENANCE',
      'DECOMMISSIONED',
    ].includes(device.status);
  }

/**
 * Returns a human-readable label for device status
 */
export function getStatusLabel(status: DeviceStatus): string {
    switch (status) {
      case "CREATED": return "作成済み";
      case "PROVISIONED": return "プロビジョン済み";
      case "ACTIVE": return "アクティブ";
      case "INACTIVE": return "非アクティブ";
      case "MAINTENANCE": return "メンテナンス";
      case "DECOMMISSIONED": return "廃止";
      default: return status;
    }
  }