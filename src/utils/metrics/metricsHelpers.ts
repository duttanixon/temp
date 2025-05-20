import { MetricsResponse, TransformedMetricData } from "@/types/metrics";

export function transformMetricData(
  metricsResponse: MetricsResponse | null,
  unitConverter?: (value: number) => number
): TransformedMetricData[] {
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
  
      // Convert value if converter is provided
      let value = parseFloat(point.value.toFixed(2));
      if (unitConverter) {
        value = parseFloat(unitConverter(value).toFixed(2));
      }

      // Add this series' value to the data point
      dataMap.get(timestamp)[series.name] = value;
    });
  });

  // Convert map to array
  return Array.from(dataMap.values());
}

export function getSeriesNames(
  metricsResponse: MetricsResponse | null
): string[] {
  if (!metricsResponse) return [];
  return metricsResponse.series.map((s) => s.name);
}

export const TIME_RANGES = [
  { value: "1h", label: "1 時間" },
  { value: "3h", label: "3 時間" },
  { value: "6h", label: "6 時間" },
  { value: "12h", label: "12 時間" },
  { value: "24h", label: "24 時間" },
];

export const LINE_COLORS = [
  "var(--primary-600)",
  "var(--success-500)",
  "var(--warning-500)",
  "var(--chart-4)",
  "var(--chart-5)",
];


export function kiloBytesToMB(kilobytes: number): number {
  return kilobytes / 1024;
}

export function kiloBytesToGB(kilobytes: number): number {
  return kilobytes / 1024 / 1024;
}