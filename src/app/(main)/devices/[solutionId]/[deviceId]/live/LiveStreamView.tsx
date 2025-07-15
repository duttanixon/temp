"use client";

import { useState } from "react";
import { Device } from "@/types/device";
import { useLiveStream } from "@/hooks/analytics/city_eye/useLiveStream";
import { Play, Square, Loader2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
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
        <h1 className="text-3xl font-bold text-gray-900">{device.name} - ライブストリーム</h1>
        <p className="mt-2 text-gray-600">
          リアルタイムでデバイスの映像を確認できます
        </p>
      </div>

      {/* Controls */}
      <Card>
        <CardHeader>
          <CardTitle>ストリーム設定</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-4">
            <div>
              <label className="text-sm font-medium text-gray-700">
                画質
              </label>
              <select
                value={quality}
                onChange={(e) => setQuality(e.target.value as "low" | "medium" | "high")}
                disabled={isStreaming}
                className="mt-1 block rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              >
                <option value="low">低画質</option>
                <option value="medium">標準画質</option>
                <option value="high">高画質</option>
              </select>
            </div>

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

            <div className="flex-1" />

            {!isStreaming ? (
              <Button
                onClick={handleStartStream}
                 disabled={isLoading || isPolling}
                className="bg-blue-600 hover:bg-blue-700"
              >
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
                variant="destructive"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    停止中...
                  </>
                ) : (
                  <>
                    <Square className="mr-2 h-4 w-4" />
                    ストリーム停止
                  </>
                )}
              </Button>
            )}
          </div>

          {/* Polling status indicator */}
          {isPolling && (
            <Alert className="bg-blue-50 border-blue-200">
              <Loader2 className="h-4 w-4 animate-spin" />
              <AlertDescription className="text-blue-800">
                ストリームを初期化しています。しばらくお待ちください...
              </AlertDescription>
            </Alert>
          )}

          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Video Player */}
      <Card>
        <CardHeader>
          <CardTitle>ライブ映像</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="relative aspect-video w-full overflow-hidden rounded-lg bg-black">
            {isStreaming && streamUrl ? (
              <VideoPlayer url={streamUrl} />
            ) : (
              <div className="flex h-full items-center justify-center">
                <p className="text-gray-500">
                  {isLoading || isPolling ? "ストリームを開始しています..." : "ストリームが開始されていません"}
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}