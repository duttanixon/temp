import { useState, useEffect, useCallback } from 'react';
import { deviceService } from '@/services/deviceService';
import { DeviceBatchStatusResponse } from '@/types/device';

interface UseBatchDeviceStatusOptions {
  refetchInterval?: number;
  enabled?: boolean;
}

export function useBatchDeviceStatus(
  deviceIds: string[],
  options?: UseBatchDeviceStatusOptions
) {
  const [statuses, setStatuses] = useState<DeviceBatchStatusResponse>({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { refetchInterval = 60000, enabled = true } = options || {}; // Default 60 seconds

  const fetchStatuses = useCallback(async () => {
    if (!deviceIds.length || !enabled) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await deviceService.getDeviceStatuses(deviceIds);
      setStatuses(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch device statuses');
      setStatuses({});
    } finally {
      setIsLoading(false);
    }
  }, [deviceIds, enabled]);

  // Initial fetch and interval setup
  useEffect(() => {
    if (!deviceIds.length || !enabled) return;

    fetchStatuses();

    // Set up polling if refetchInterval is provided
    if (refetchInterval > 0) {
      const interval = setInterval(fetchStatuses, refetchInterval);
      return () => clearInterval(interval);
    }
  }, [deviceIds.join(','), enabled, refetchInterval, fetchStatuses]);

  return {
    statuses,
    isLoading,
    error,
    refetch: fetchStatuses,
  };
}