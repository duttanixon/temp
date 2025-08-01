"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { useLiveStream } from "@/hooks/analytics/city_eye/useLiveStream";
import { Device } from "@/types/device";
import { Loader2, Play, Square } from "lucide-react";
import { useState } from "react";
import VideoPlayer from "./VideoPlayer";

interface LiveStreamViewProps {
  device: Device;
}

export default function LiveStreamView({ device }: LiveStreamViewProps) {
  const {
    isLoading,
    isStreaming,
    streamUrl,
    error,
    startStream,
    stopStream,
    isPolling,
  } = useLiveStream(device.device_id);

  const [quality, setQuality] = useState<"low" | "medium" | "high">("medium");
  const [duration, setDuration] = useState(240); // 4 minutes default

  const handleStartStream = () => {
    startStream(duration, quality);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">
          {device.name} - ライブストリーム
        </h1>
        <p className="mt-2 text-gray-600">
          リアルタイムでデバイスの映像を確認できます
        </p>
      </div>

      {/* Video Player */}
      <Card>
        <CardHeader>
          <div className="flex items-end justify-between">
            <div className="flex items-center gap-6">
              <div>
                <label className="text-sm font-medium text-gray-700">
                  継続時間（秒）
                </label>
                <input
                  type="number"
                  value={duration}
                  onChange={(e) => setDuration(parseInt(e.target.value))}
                  min={60}
                  max={3600}
                  step={60}
                  disabled={isStreaming}
                  className="mt-1 block w-24 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                />
              </div>
            </div>
            {!isStreaming ? (
              <Button
                onClick={handleStartStream}
                disabled={isLoading || isPolling}
                className="bg-blue-600 hover:bg-blue-700">
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    {isPolling ? "初期化中..." : "開始中..."}
                  </>
                ) : (
                  <>
                    <Play className="mr-2 h-4 w-4" />
                    ストリーム開始
                  </>
                )}
              </Button>
            ) : (
              <Button
                onClick={stopStream}
                disabled={isLoading}
                variant="destructive">
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 size-4 animate-spin" />
                    停止中...
                  </>
                ) : (
                  <>
                    <Square className="mr-2 size-4" />
                    ストリーム停止
                  </>
                )}
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <div className="relative aspect-video w-full overflow-hidden rounded-lg bg-black">
            {isStreaming && streamUrl ? (
              <VideoPlayer url={streamUrl} />
            ) : (
              <>
                <div className="flex h-full items-center justify-center">
                  {isLoading || isPolling ? (
                    <div className="flex flex-col items-center gap-2">
                      <Loader2 className="size-8 animate-spin text-gray-400" />
                      <span className="text-gray-400">
                        ストリームを開始しています...
                      </span>
                    </div>
                  ) : (
                    /* Play Button */
                    <div
                      className="flex flex-col items-center justify-center gap-4 transition-all duration-300 hover:scale-105 cursor-pointer"
                      onClick={handleStartStream}>
                      <div className="size-20 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-2xl transition-all duration-300 group-hover:shadow-indigo-500/40 group-hover:scale-110">
                        {/* <svg
                        className="size-8 text-white"
                        fill="currentColor"
                        viewBox="0 0 24 24">
                        <path d="M8 5v14l11-7z" />
                      </svg> */}
                        <Play className="size-8 fill-white stroke-white" />
                      </div>
                    </div>
                  )}
                </div>
                <div className="absolute top-4 right-4 backdrop-blur-md">
                  <div className="flex items-center gap-2 bg-white/10 backdrop-blur-sm px-3 py-1.5 rounded-full border border-white/20">
                    <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
                    <span className="text-white/60 font-medium text-xs">
                      待機中
                    </span>
                  </div>
                </div>
              </>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
