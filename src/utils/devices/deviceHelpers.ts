import { Device, DeviceStatus } from '@/types/device';

/**
 * Determines if a device can be provisioned based on its current status
 */
export function canProvisionDevice(device: Device): boolean {
    return device.status === 'CREATED';
  }

/**
 * Determines if a device can be activated based on its current status
 */
export function canActivateDevice(device: Device): boolean {
    return device.status === 'PROVISIONED' || device.status === 'INACTIVE';
  }


/**
 * Determines if a device can be decommissioned based on its current status
 */
export function canDecommissionDevice(device: Device): boolean {
    return device.status !== 'DECOMMISSIONED';
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
 * Returns the appropriate CSS class for the status indicator based on device status
 */
export function getStatusColor(status: DeviceStatus, isOnline: boolean): string {
    if (isOnline) return "bg-green-500";
    
    switch (status) {
      case "ACTIVE": return "bg-blue-500";
      case "PROVISIONED": return "bg-yellow-500";
      case "INACTIVE": return "bg-gray-500";
      case "MAINTENANCE": return "bg-orange-500";
      case "DECOMMISSIONED": return "bg-red-500";
      default: return "bg-gray-500";
    }
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