import { DeviceStatus } from '@/types/device';
import { getStatusColor, getStatusLabel } from '@/utils/devices/deviceHelpers';


type DeviceStatusBadgeProps = {
    status: DeviceStatus;
    isOnline: boolean;
    showLabel?: boolean;
    size?: 'sm' | 'md';
  };

export default function DeviceStatusBadge({ 
    status, 
    isOnline, 
    showLabel = true,
    size = 'md' 
  }: DeviceStatusBadgeProps) {
    const bgColor = getStatusColor(status, isOnline);
    const label = getStatusLabel(status);

    // Size classes for the indicator dot
    const dotSize = size === 'sm' ? 'h-2 w-2' : 'h-2.5 w-2.5';
    const textSize = size === 'sm' ? 'text-xs' : 'text-sm';

    return (
        <span className="inline-flex items-center">
          <span className={`${dotSize} rounded-full ${bgColor} mr-2`}></span>
          {showLabel && (
            <>
              <span className={`${textSize} text-[#2C3E50]`}>
                {label}
              </span>
              {isOnline && <span className="ml-2 text-green-600">(オンライン)</span>}
            </>
          )}
        </span>
      );
    }