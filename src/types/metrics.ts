export type MetricDataPoint = {
  timestamp: string;
  value: number;
  hasData?: boolean; // Optional field to indicate if data exists
};

export type MetricSeries = {
  name: string;
  data: MetricDataPoint[];
};

export type MetricsResponse = {
  series: MetricSeries[];
  device_name: string;
  start_time: string;
  end_time: string;
  interval: string;
};

export type TimeRange = {
  value: string;
  label: string;
};

export type TransformedMetricData = {
  timestamp: string;
  fullTimestamp: string; // New field for tooltip display
  hasData?: boolean; // Optional field to indicate if data exists
  [key: string]: any;
};
