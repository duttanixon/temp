import { SolutionStatus } from '@/types/solution';

/**
 * Returns a human-readable label for solution status
 */
export function getStatusLabel(status: SolutionStatus): string {
  switch (status) {
    case "ACTIVE": return "有効";
    case "BETA": return "ベータ版";
    case "DEPRECATED": return "DEPRECATED";
    default: return status;
  }
}

/**
 * Returns the appropriate CSS class for the status indicator
 */
export function getStatusColor(status: SolutionStatus): string {
  switch (status) {
    case "ACTIVE": return "bg-green-500";
    case "BETA": return "bg-blue-500";
    case "DEPRECATED": return "bg-orange-500";
    default: return "bg-gray-500";
  }
}

/**
 * Determines if a solution can be deprecated
 */
export function canDeprecateSolution(status: SolutionStatus): boolean {
  return status === 'ACTIVE' || status === 'BETA';
}

/**
 * Determines if a solution can be activated
 */
export function canActivateSolution(status: SolutionStatus): boolean {
  return status === 'DEPRECATED';
}

/**
 * Returns a formatted label for device compatibility
 */
export function formatDeviceType(deviceType: string): string {
  switch (deviceType) {
    case "NVIDIA_JETSON": return "NVIDIA Jetson";
    case "RASPBERRY_PI": return "Raspberry Pi";
    default: return deviceType;
  }
}