import { useState, useCallback, useRef, useEffect } from 'react';
import { toast } from 'sonner';
import { deviceService } from '@/services/deviceService';
import {
  DeviceStreamStatus,
} from "@/types/device";

interface LiveStreamState {
  isLoading: boolean;
  isStreaming: boolean;
  streamUrl: string | null;
  streamName: string | null;
  messageId: string | null;
  error: string | null;
  isPolling: boolean;
}

export const useLiveStream = (deviceId: string) => {
  const [state, setState] = useState<LiveStreamState>({
    isLoading: false,
    isStreaming: false,
    streamUrl: null,
    streamName: null,
    messageId: null,
    error: null,
    isPolling: false,
  });

  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const maxPollAttemptsRef = useRef<number>(0);

  // Function to check stream status
  const checkStreamStatus = useCallback(async (): Promise<DeviceStreamStatus | null> => {
    try {
      const response = await deviceService.getStreamStatus(deviceId);
      return response;
    } catch (error) {
      console.error('Failed to check stream status:', error);
      return null;
    }
  }, [deviceId]);

  // Function to start polling for stream status
  const startPolling = useCallback(() => {
    setState(prev => ({ ...prev, isPolling: true }));
    maxPollAttemptsRef.current = 0;
    const maxAttempts = 24; // 2 minutes with 5-second intervals

    pollingIntervalRef.current = setInterval(async () => {
      maxPollAttemptsRef.current++;
      
      const status = await checkStreamStatus();
      
      if (status && status.kvs_url) {
        // Stream is ready
        setState(prev => ({
          ...prev,
          isLoading: false,
          isStreaming: true,
          streamUrl: status.kvs_url,
          streamName: status.stream_name,
          error: null,
          isPolling: false,
        }));
        
        toast.success('Live stream is ready!');

        // Stop polling
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
      } else if (maxPollAttemptsRef.current >= maxAttempts) {
        // Max attempts reached
        setState(prev => ({
          ...prev,
          isLoading: false,
          error: 'Stream initialization timed out. Please try again.',
          isPolling: false,
        }));
        
        toast.error('Stream initialization timed out');
        
        // Stop polling
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
      }
    }, 5000); // Poll every 5 seconds
  }, [checkStreamStatus]);

  // Clean up polling on unmount
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);

  const startStream = useCallback(async (duration?: number, quality?: string) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      const response = await deviceService.startLiveStream(deviceId, duration, quality);
      
      // Store messageId and streamName from the response
      setState(prev => ({
        ...prev,
        messageId: response.message_id,
        streamName: response.stream_name,
      }));
      
      if (response.kvs_url) {
        // Stream URL is immediately available
        setState(prev => ({
          ...prev,
          isLoading: false,
          isStreaming: true,
          streamUrl: response.kvs_url,
          error: null,
        }));
        toast.success('Live stream started successfully!');
      } else {
        // Stream URL not available yet, start polling
        toast.info('Initializing stream, please wait...');
        startPolling();
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to start stream',
      }));
      toast.error('Failed to start live stream');
    }
  }, [deviceId, startPolling]);

  const stopStream = useCallback(async () => {
    // Stop any ongoing polling
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
    
    setState(prev => ({ ...prev, isLoading: true, isPolling: false }));
    
    try {
      await deviceService.stopLiveStream(deviceId);
      setState({
        isLoading: false,
        isStreaming: false,
        streamUrl: null,
        streamName: null,
        messageId: null,
        error: null,
        isPolling: false,
      });
      toast.success('Live stream stopped');
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to stop stream',
      }));
      toast.error('Failed to stop live stream');
    }
  }, [deviceId]);

  return {
    ...state,
    startStream,
    stopStream,
  };
};
