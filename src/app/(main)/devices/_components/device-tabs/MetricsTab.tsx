// export default function MetricsTab() {
//   return (
//     <div className="bg-inherit p-2 flex flex-col md:flex-row gap-4 items-stretch justify-center rounded-b-lg">
//       <div className="bg-white p-4 rounded-lg shadow flex-1">
//         <h2 className="text-lg font-semibold mb-2">Metrics Card 1</h2>
//         <p className="text-gray-600">Content for the first metrics card</p>
//       </div>

//       <div className="bg-white p-4 rounded-lg shadow flex-1">
//         <h2 className="text-lg font-semibold mb-2">Metrics Card 2</h2>
//         <p className="text-gray-600">Content for the second metrics card</p>
//       </div>
//       <div className="bg-white p-4 rounded-lg shadow flex-1">
//         <h2 className="text-lg font-semibold mb-2">Metrics Card 2</h2>
//         <p className="text-gray-600">Content for the second metrics card</p>
//       </div>
//     </div>
//   );
// }
"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { getSession } from "next-auth/react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

// Define metric types
type MetricDataPoint = {
  timestamp: string;
  value: number;
};

type MetricSeries = {
  name: string;
  data: MetricDataPoint[];
};

type MetricsResponse = {
  series: MetricSeries[];
  device_name: string;
  start_time: string;
  end_time: string;
  interval: string;
};

// Time range options
const timeRanges = [
  { value: "1h", label: "1 時間" },
  { value: "3h", label: "3 時間" },
  { value: "6h", label: "6 時間" },
  { value: "12h", label: "12 時間" },
  { value: "24h", label: "24 時間" },
];

export default function MetricsTab() {
  const params = useParams();
  const deviceId = params?.deviceId as string;

  // State variables
  const [deviceName, setDeviceName] = useState<string>("");
  const [timeRange, setTimeRange] = useState<string>("1h");
  const [memoryMetrics, setMemoryMetrics] = useState<MetricsResponse | null>(
    null
  );
  const [cpuMetrics, setCpuMetrics] = useState<MetricsResponse | null>(null);
  const [diskMetrics, setDiskMetrics] = useState<MetricsResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch device name first - we need this for metrics API
  useEffect(() => {
    async function fetchDeviceName() {
      try {
        const session = await getSession();
        if (!session?.accessToken) return;

        const response = await fetch(
          `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/devices/${deviceId}`,
          {
            headers: {
              Authorization: `Bearer ${session.accessToken}`,
            },
          }
        );

        if (!response.ok) throw new Error("Failed to fetch device information");

        const deviceData = await response.json();
        setDeviceName(deviceData.name);
      } catch (err) {
        setError("デバイス情報の取得に失敗しました");
        console.error("Error fetching device:", err);
      }
    }

    if (deviceId) {
      fetchDeviceName();
    }
  }, [deviceId]);

  // Fetch all metrics when device name is available or time range changes
  useEffect(() => {
    if (!deviceName) return;

    async function fetchMetrics() {
      setIsLoading(true);
      setError(null);

      try {
        const session = await getSession();
        if (!session?.accessToken) return;

        // Calculate time range based on selection
        const endTime = new Date().toISOString();
        const hoursToSubtract = parseInt(timeRange.replace("h", ""));
        const startTime = new Date(
          Date.now() - hoursToSubtract * 60 * 60 * 1000
        ).toISOString();

        // Create the base URL with common params
        const baseUrl = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/device-metrics`;
        const params = `?device_name=${deviceName}&start_time=${startTime}&end_time=${endTime}`;

        // Fetch all metrics in parallel
        const [memoryRes, cpuRes, diskRes] = await Promise.all([
          fetch(`${baseUrl}/memory${params}`, {
            headers: { Authorization: `Bearer ${session.accessToken}` },
          }),
          fetch(`${baseUrl}/cpu${params}`, {
            headers: { Authorization: `Bearer ${session.accessToken}` },
          }),
          fetch(`${baseUrl}/disk${params}`, {
            headers: { Authorization: `Bearer ${session.accessToken}` },
          }),
        ]);

        // Check for errors
        if (!memoryRes.ok || !cpuRes.ok || !diskRes.ok) {
          throw new Error("One or more metrics requests failed");
        }

        // Parse responses
        const memoryData = await memoryRes.json();
        const cpuData = await cpuRes.json();
        const diskData = await diskRes.json();

        // Update state
        setMemoryMetrics(memoryData);
        setCpuMetrics(cpuData);
        setDiskMetrics(diskData);
      } catch (err) {
        setError("メトリクスの取得に失敗しました");
        console.error("Error fetching metrics:", err);
      } finally {
        setIsLoading(false);
      }
    }

    fetchMetrics();
  }, [deviceName, timeRange]);

  // Function to transform metric data for Recharts
  const transformMetricData = (metricsResponse: MetricsResponse | null) => {
    if (!metricsResponse) return [];

    // Create a map of timestamps to data points
    const dataMap = new Map();

    // Process each series
    metricsResponse.series.forEach((series) => {
      series.data.forEach((point) => {
        const timestamp = new Date(point.timestamp).toLocaleTimeString();
        if (!dataMap.has(timestamp)) {
          dataMap.set(timestamp, { timestamp });
        }

        // Add this series' value to the data point
        dataMap.get(timestamp)[series.name] = parseFloat(
          point.value.toFixed(2)
        );
      });
    });

    // Convert map to array
    return Array.from(dataMap.values());
  };

  // Get series names for a metric (for legend)
  const getSeriesNames = (metricsResponse: MetricsResponse | null) => {
    if (!metricsResponse) return [];
    return metricsResponse.series.map((s) => s.name);
  };

  // Refresh button handler
  const handleRefresh = () => {
    if (deviceName) {
      setMemoryMetrics(null);
      setCpuMetrics(null);
      setDiskMetrics(null);
      setIsLoading(true);
    }
  };

  // Line colors for the graphs - using color variables from globals.css where possible
  const lineColors = [
    "var(--primary-600)",
    "var(--success-500)",
    "var(--warning-500)",
    "var(--chart-4)",
    "var(--chart-5)",
  ];

  // Create a reusable graph component
  const MetricGraph = ({
    title,
    data,
    seriesNames,
    unit,
  }: {
    title: string;
    data: any[];
    seriesNames: string[];
    unit: string;
  }) => (
    <div className="bg-white p-4 rounded-lg shadow flex-1">
      <h2 className="text-lg font-semibold mb-2 text-[var(--text-primary)]">
        {title}
      </h2>
      {isLoading ? (
        <div className="h-64 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--primary-500)]"></div>
        </div>
      ) : data.length === 0 ? (
        <div className="h-64 flex items-center justify-center text-[var(--text-tertiary)]">
          データがありません
        </div>
      ) : (
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={data}
              margin={{ top: 5, right: 20, left: 0, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="timestamp"
                tick={{ fill: "var(--text-secondary)" }}
                tickLine={{ stroke: "var(--border)" }}
              />
              <YAxis
                unit={unit}
                tick={{ fill: "var(--text-secondary)" }}
                tickLine={{ stroke: "var(--border)" }}
              />
              <Tooltip
                formatter={(value) => [`${value} ${unit}`, ""]}
                contentStyle={{
                  backgroundColor: "var(--background)",
                  borderColor: "var(--border)",
                  color: "var(--text-primary)",
                }}
              />
              <Legend />
              {seriesNames.map((name, index) => (
                <Line
                  key={name}
                  type="monotone"
                  dataKey={name}
                  stroke={lineColors[index % lineColors.length]}
                  activeDot={{ r: 6 }}
                  strokeWidth={2}
                  name={name}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );

  return (
    <div className="space-y-4 p-3">
      {/* Controls */}
      <div className="bg-white p-4 rounded-lg shadow flex justify-between items-center">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-[var(--text-secondary)]">
            期間:
          </span>
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {timeRanges.map((range) => (
                <SelectItem key={range.value} value={range.value}>
                  {range.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={handleRefresh}
          disabled={isLoading || !deviceName}
          className="hover:bg-[var(--btn-secondary-hover)]"
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          更新
        </Button>
      </div>

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
        />
        <MetricGraph
          title="CPU 使用率"
          data={transformMetricData(cpuMetrics)}
          seriesNames={getSeriesNames(cpuMetrics)}
          unit="%"
        />
        <MetricGraph
          title="ディスク使用率"
          data={transformMetricData(diskMetrics)}
          seriesNames={getSeriesNames(diskMetrics)}
          unit="GB"
        />
      </div>
    </div>
  );
}
