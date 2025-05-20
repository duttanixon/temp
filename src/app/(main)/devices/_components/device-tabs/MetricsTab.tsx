"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { MetricsResponse } from "@/types/metrics";
import { metricsService } from "@/services/metricsService";
import { transformMetricData, getSeriesNames } from "@/utils/metrics/metricsHelpers";
import MetricGraph from "./metrics/MetricGraph";
import MetricsControls from "./metrics/MetricsControls";

export default function MetricsTab() {
  const params = useParams();
  const deviceId = params?.deviceId as string;

  // State variables
  const [deviceName, setDeviceName] = useState<string>("");
  const [timeRange, setTimeRange] = useState<string>("1h");
  const [memoryMetrics, setMemoryMetrics] = useState<MetricsResponse | null>(null);
  const [cpuMetrics, setCpuMetrics] = useState<MetricsResponse | null>(null);
  const [diskMetrics, setDiskMetrics] = useState<MetricsResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch device name first
  useEffect(() => {
    async function fetchDeviceName() {
      if (!deviceId) return;
      
      try {
        const name = await metricsService.getDeviceName(deviceId);
        setDeviceName(name);
      } catch (err) {
        setError("デバイス情報の取得に失敗しました");
        console.error("Error fetching device:", err);
      }
    }

    fetchDeviceName();
  }, [deviceId]);

  // Fetch metrics when device name is available or time range changes
  useEffect(() => {
    if (!deviceName) return;

    async function fetchMetrics() {
      setIsLoading(true);
      setError(null);

      try {
        const { memory, cpu, disk } = await metricsService.getAllMetrics(deviceName, timeRange);
        
        setMemoryMetrics(memory);
        setCpuMetrics(cpu);
        setDiskMetrics(disk);
      } catch (err) {
        setError("メトリクスの取得に失敗しました");
        console.error("Error fetching metrics:", err);
      } finally {
        setIsLoading(false);
      }
    }

    fetchMetrics();
  }, [deviceName, timeRange]);

  // Refresh handler
  const handleRefresh = () => {
    if (deviceName) {
      setMemoryMetrics(null);
      setCpuMetrics(null);
      setDiskMetrics(null);
      setIsLoading(true);
      
      // The useEffect will trigger a refetch when isLoading changes
      setTimeRange(timeRange); // Trigger the useEffect without changing the value
    }
  };

  return (
    <div className="space-y-4 p-3">
      {/* Controls */}
      <MetricsControls
        timeRange={timeRange}
        setTimeRange={setTimeRange}
        onRefresh={handleRefresh}
        isLoading={isLoading}
        isDisabled={!deviceName}
      />

      {/* Error message */}
      {error && (
        <div className="bg-red-50 p-4 rounded-lg text-[var(--danger-600)] border border-[var(--danger-200)]">
          <p>{error}</p>
        </div>
      )}

      {/* Graphs */}
      <div className="flex flex-col lg:flex-row gap-4">
        <MetricGraph
          title="メモリ使用率"
          data={transformMetricData(memoryMetrics)}
          seriesNames={getSeriesNames(memoryMetrics)}
          unit="MB"
          isLoading={isLoading}
        />
        <MetricGraph
          title="CPU 使用率"
          data={transformMetricData(cpuMetrics)}
          seriesNames={getSeriesNames(cpuMetrics)}
          unit="%"
          isLoading={isLoading}
        />
        <MetricGraph
          title="ディスク使用率"
          data={transformMetricData(diskMetrics)}
          seriesNames={getSeriesNames(diskMetrics)}
          unit="GB"
          isLoading={isLoading}
        />
      </div>
    </div>
  );
}