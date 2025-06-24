import { useState, useCallback } from 'react';
import { toast } from 'sonner';
import { deviceService } from '@/services/deviceService';


interface LiveStreamState {
  isLoading: boolean;
  isStreaming: boolean;
  streamUrl: string | null;
  streamName: string | null;
  messageId: string | null;
  error: string | null;
}


export const useLiveStream = (deviceId: string) => {
  const [state, setState] = useState<LiveStreamState>({
    isLoading: false,
    isStreaming: false,
    streamUrl: null,
    streamName: null,
    messageId: null,
    error: null,
  });

  const startStream = useCallback(async (duration?: number, quality?: string) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      const response = await deviceService.startLiveStream(deviceId, duration, quality);
      
      // Since backend returns the response directly with kvs_url
      if (response.kvs_url) {
        setState({
          isLoading: false,
          isStreaming: true,
          streamUrl: response.kvs_url,
          streamName: response.stream_name,
          messageId: response.message_id,
          error: null,
        });
        toast.success('Live stream started successfully!');
      } else {
        // If kvs_url is null, the stream might still be initializing
        setState(prev => ({
          ...prev,
          isLoading: false,
          error: 'Stream URL not available yet. Please try again.',
        }));
        toast.warning('Stream is initializing. Please try again in a moment.');
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to start stream',
      }));
      toast.error('Failed to start live stream');
    }
  }, [deviceId]);

  const stopStream = useCallback(async () => {
    setState(prev => ({ ...prev, isLoading: true }));
    
    try {
      await deviceService.stopLiveStream(deviceId);
      setState({
        isLoading: false,
        isStreaming: false,
        streamUrl: null,
        streamName: null,
        messageId: null,
        error: null,
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
