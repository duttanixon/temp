import { MetricsResponse, TransformedMetricData } from "@/types/metrics";

export function transformMetricData(
  metricsResponse: MetricsResponse | null,
  unitConverter?: (value: number) => number
): TransformedMetricData[] {
  if (!metricsResponse) return [];

  // Create a map of timestamps to data points
  const dataMap = new Map();

  // Check if the date range spans multiple days
  let isMultipleDays = false;
  if (metricsResponse.start_time && metricsResponse.end_time) {
    const startTime = new Date(metricsResponse.start_time);
    const endTime = new Date(metricsResponse.end_time);
    // Check if the date range is more than 24 hours
    isMultipleDays = (endTime.getTime() - startTime.getTime()) > (24 * 60 * 60 * 1000);
  }

  // Process each series
  metricsResponse.series.forEach((series) => {
    series.data.forEach((point) => {
      // Keep the original ISO timestamp for sorting
      const originalTimestamp = new Date(point.timestamp);
      
      // Format the timestamp based on whether it spans multiple days
      let displayTimestamp;
      if (isMultipleDays) {
        // Include date for multi-day ranges (e.g., "MM/DD HH:MM")
        displayTimestamp = originalTimestamp.toLocaleDateString('ja-JP', {
          month: 'numeric',
          day: 'numeric',
        }) + ' ' + originalTimestamp.toLocaleTimeString('ja-JP', {
          hour: '2-digit',
          minute: '2-digit',
        });
      } else {
        // Just time for single day (e.g., "HH:MM")
        displayTimestamp = originalTimestamp.toLocaleTimeString('ja-JP', {
          hour: '2-digit',
          minute: '2-digit',
        });
      }

      // Store the formatted date for the tooltip (DD/MM/YYYY format)
      const formattedDate = originalTimestamp.toLocaleDateString('ja-JP', {
        day: 'numeric',
        month: 'numeric',
        year: 'numeric',
      });
      const formattedTime = originalTimestamp.toLocaleTimeString('ja-JP', {
        hour: '2-digit',
        minute: '2-digit',
      });
      

      
      // Use the formatted timestamp as the key
      if (!dataMap.has(displayTimestamp)) {
        dataMap.set(displayTimestamp, { 
          timestamp: displayTimestamp,
          fullTimestamp: `${formattedDate} ${formattedTime}`,
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