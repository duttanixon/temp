"use client";

import { metricsService } from "@/services/metricsService";
import { MetricsResponse } from "@/types/metrics";
import {
  getSeriesNames,
  kiloBytesToGB,
  kiloBytesToMB,
  transformMetricData,
} from "@/utils/metrics/metricsHelpers";
import { endOfDay, format, startOfDay } from "date-fns";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import MetricGraph from "./metrics/MetricGraph";
import MetricsControls from "./metrics/MetricsControls";

export default function MetricsTab() {
  const params = useParams();
  const deviceId = params?.deviceId as string;

  // State variables
  const [deviceName, setDeviceName] = useState<string>("");
  const [timeRange, setTimeRange] = useState<string>("1h");
  const [refreshTrigger, setRefreshTrigger] = useState<number>(0);
  const [memoryMetrics, setMemoryMetrics] = useState<MetricsResponse | null>(
    null
  );
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
        const { memory, cpu, disk } = await metricsService.getAllMetrics(
          deviceName,
          timeRange
        );
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
  }, [deviceName, timeRange, refreshTrigger]);

  // Refresh handler
  const handleRefresh = () => {
    if (deviceName) {
      setMemoryMetrics(null);
      setCpuMetrics(null);
      setDiskMetrics(null);
      setIsLoading(true);
      setRefreshTrigger((prev) => prev + 1);
    }
  };

  const handleDateRangeChange = async (from: Date, to: Date) => {
    if (!deviceName) return;

    setIsLoading(true);
    setError(null);

    try {
      const adjustedFrom = startOfDay(from);
      const adjustedTo = endOfDay(to);

      // Format dates for API
      // Using "yyyy-MM-dd'T'HH:mm:ssXXX" includes the timezone offset, e.g., +09:00
      // The backend (timestream.py) converts these to UTC.
      const startTime = format(adjustedFrom, "yyyy-MM-dd'T'HH:mm:ssXXX");
      const endTime = format(adjustedTo, "yyyy-MM-dd'T'HH:mm:ssXXX");

      // Calculate appropriate interval based on date range (in minutes)
      // const diffHours =
      //   (adjustedTo.getTime() - adjustedFrom.getTime()) / (1000 * 60 * 60);
      const interval = 5; // default 5 minutes

      // if (diffHours > 72)
      //   interval = 60; // 1 hour intervals for > 3 days
      // else if (diffHours > 24)
      //   interval = 30; // 30 min intervals for > 1 day
      // else if (diffHours > 12) interval = 15; // 15 min intervals for > 12 hours

      // Fetch metrics with custom date range
      const memory = await metricsService.getMetrics(
        deviceName,
        "memory",
        "custom",
        startTime,
        endTime,
        interval
      );
      const cpu = await metricsService.getMetrics(
        deviceName,
        "cpu",
        "custom",
        startTime,
        endTime,
        interval
      );
      const disk = await metricsService.getMetrics(
        deviceName,
        "disk",
        "custom",
        startTime,
        endTime,
        interval
      );

      setMemoryMetrics(memory);
      setCpuMetrics(cpu);
      setDiskMetrics(disk);
    } catch (err) {
      setError("メトリクスの取得に失敗しました");
      console.error("Error fetching metrics with custom date range:", err);
    } finally {
      setIsLoading(false);
    }
  };

  // Custom formatters for different units
  const memoryFormatter = (value: number) => `${value.toFixed(0)}`;
  const cpuFormatter = (value: number) => `${value.toFixed(0)}`;
  const diskFormatter = (value: number) => `${value.toFixed(1)}`;

  return (
    <div className="space-y-4 p-3">
      {/* Controls */}
      <MetricsControls
        timeRange={timeRange}
        setTimeRange={setTimeRange}
        onRefresh={handleRefresh}
        isLoading={isLoading}
        isDisabled={!deviceName}
        onDateRangeChange={handleDateRangeChange}
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
          data={transformMetricData(memoryMetrics, kiloBytesToMB)}
          seriesNames={getSeriesNames(memoryMetrics)}
          unit="MB"
          isLoading={isLoading}
          domain={[0, 8000]} // Start from 0, auto-scale the max
          tickFormatter={memoryFormatter}
          axisFontSize={10}
        />
        <MetricGraph
          title="CPU 使用率"
          data={transformMetricData(cpuMetrics)}
          seriesNames={getSeriesNames(cpuMetrics)}
          unit="%"
          isLoading={isLoading}
          domain={[0, 100]} // CPU percentage: 0-100%
          tickFormatter={cpuFormatter}
          axisFontSize={10}
        />
        <MetricGraph
          title="ディスク使用率"
          data={transformMetricData(diskMetrics, kiloBytesToGB)}
          seriesNames={getSeriesNames(diskMetrics)}
          unit="MB"
          isLoading={isLoading}
          domain={[0, 1000]} // Start from 0, auto-scale the max
          tickFormatter={diskFormatter}
          axisFontSize={10}
        />
      </div>
    </div>
  );
}
