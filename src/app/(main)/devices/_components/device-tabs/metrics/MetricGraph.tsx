import { ResponsiveContainer, LineChart, CartesianGrid, XAxis, YAxis, Tooltip, Legend, Line } from 'recharts';
import { LINE_COLORS } from '@/utils/metrics/metricsHelpers';
import { TransformedMetricData } from '@/types/metrics';

interface MetricGraphProps {
  title: string;
  data: TransformedMetricData[];
  seriesNames: string[];
  unit: string;
  isLoading: boolean;
  domain?: [number, number];
  tickFormatter?: (value: number) => string;
  axisFontSize?: number;
}

export default function MetricGraph({
  title,
  data,
  seriesNames,
  unit,
  isLoading,
  domain,
  tickFormatter,
  axisFontSize = 12,
}: MetricGraphProps) {
  const getLabelContent = (label: string) => {
    const dataPoint = data.find((d) => d.timestamp === label);
    return dataPoint?.fullTimestamp || label;
  };
  
    return (
        <div className="bg-white p-4 rounded-lg shadow flex-1">
          <h2 className="text-base font-semibold mb-2 text-[var(--text-primary)]">
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
                    tick={{ fill: "var(--text-secondary)", fontSize: axisFontSize }}
                    tickLine={{ stroke: "var(--border)" }}
                  />
                  <YAxis
                    domain={domain || ['auto', 'auto']}
                    unit={unit}
                    tickFormatter={tickFormatter}
                    tick={{ fill: "var(--text-secondary)", fontSize: axisFontSize  }}
                    tickLine={{ stroke: "var(--border)" }}
                  />
                  <Tooltip
                  labelFormatter={(label) => getLabelContent(label)}
                    formatter={(value) => [`${tickFormatter ? tickFormatter(value as number) : value} ${unit}`, ""]}
                    contentStyle={{
                      backgroundColor: "var(--background)",
                      borderColor: "var(--border)",
                      color: "var(--text-primary)",
                      fontSize: axisFontSize,
                    }}
                  />
                  <Legend />
                  {seriesNames.map((name, index) => (
                    <Line
                      key={name}
                      type="monotone"
                      dataKey={name}
                      stroke={LINE_COLORS[index % LINE_COLORS.length]}
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
}  