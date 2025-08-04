"use client";

import Hls from "hls.js";
import { useEffect, useRef } from "react";

interface VideoPlayerProps {
  url: string;
}

export default function VideoPlayer({ url }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video || !url) return;

    if (Hls.isSupported()) {
      const hls = new Hls({
        enableWorker: true,
        lowLatencyMode: true,
        backBufferLength: 90,
      });

      hls.loadSource(url);
      hls.attachMedia(video);

      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        video.play().catch(() => {
          console.log("Autoplay was prevented");
        });
      });

      return () => {
        hls.destroy();
      };
    } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
      // For Safari
      video.src = url;
      video.addEventListener("loadedmetadata", () => {
        video.play().catch(() => {
          console.log("Autoplay was prevented");
        });
      });
    }
  }, [url]);

  return (
    <div className="relative size-full">
      <video
        ref={videoRef}
        className="h-full w-full"
        controls
        playsInline
        muted
      />
      {/* Status Indicator */}
      <div className="absolute top-4 right-4 backdrop-blur-md">
        <div className="flex items-center gap-2 bg-gradient-to-r from-red-600 to-red-500 px-4 py-2 rounded-full shadow-lg shadow-red-500/25 border border-red-400/30">
          <div className="relative">
            <div className="w-2.5 h-2.5 bg-white rounded-full animate-pulse"></div>
            <div className="absolute inset-0 w-2.5 h-2.5 bg-white rounded-full animate-ping opacity-75"></div>
          </div>
          <span className="text-white font-bold text-xs tracking-wider">
            LIVE
          </span>
        </div>
      </div>
    </div>
  );
}
