export type MetricDataPoint = {
  timestamp: string;
  value: number;
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
  [key: string]: any;
};
