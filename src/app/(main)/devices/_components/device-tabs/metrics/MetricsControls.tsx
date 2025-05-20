import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { RefreshCw } from "lucide-react";
import { TIME_RANGES } from "@/utils/metrics/metricsHelpers";
import { TimeRange } from "@/types/metrics";

interface MetricsControlsProps {
  timeRange: string;
  setTimeRange: (value: string) => void;
  onRefresh: () => void;
  isLoading: boolean;
  isDisabled: boolean;
}

export default function MetricsControls({
  timeRange,
  setTimeRange,
  onRefresh,
  isLoading,
  isDisabled,
}: MetricsControlsProps) {
  return (
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
            {TIME_RANGES.map((range) => (
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
        onClick={onRefresh}
        disabled={isLoading || isDisabled}
        className="hover:bg-[var(--btn-secondary-hover)]"
      >
        <RefreshCw className="h-4 w-4 mr-2" />
        更新
      </Button>
    </div>
  );
}