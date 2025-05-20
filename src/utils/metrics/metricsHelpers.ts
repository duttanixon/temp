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
      // Keep the original ISO timestamp for sorting
      const originalTimestamp = new Date(point.timestamp);
      
      // Format the timestamp more concisely
      const displayTimestamp = originalTimestamp.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
      });
      
      // Use the formatted timestamp as the key
      if (!dataMap.has(displayTimestamp)) {
        dataMap.set(displayTimestamp, { 
          timestamp: displayTimestamp,
          // Store the original timestamp for sorting
          _originalTimestamp: originalTimestamp.getTime() 
        });
      }
  
      // Convert value if converter is provided
      let value = parseFloat(point.value.toFixed(2));
      if (unitConverter) {
        value = parseFloat(unitConverter(value).toFixed(2));
      }

      // Add this series' value to the data point
      dataMap.get(displayTimestamp)[series.name] = value;
    });
  });

  // Convert map to array and sort by original timestamp
  const dataArray = Array.from(dataMap.values());
  dataArray.sort((a, b) => a._originalTimestamp - b._originalTimestamp);
  
  // Remove the _originalTimestamp property as we don't need it in the chart
  return dataArray.map(item => {
    const { _originalTimestamp, ...rest } = item;
    return rest;
  });
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