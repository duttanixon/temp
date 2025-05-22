import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { RefreshCw, Calendar } from "lucide-react";
import { TIME_RANGES } from "@/utils/metrics/metricsHelpers";
import { DateRange } from "react-day-picker";
import { DatePickerWithRange } from "@/components/ui/date-range-picker";
import { useState } from "react";

interface MetricsControlsProps {
  timeRange: string;
  setTimeRange: (value: string) => void;
  onRefresh: () => void;
  isLoading: boolean;
  isDisabled: boolean;
  onDateRangeChange?: (from: Date, to: Date) => void;
}

export default function MetricsControls({
  timeRange,
  setTimeRange,
  onRefresh,
  isLoading,
  isDisabled,
  onDateRangeChange,
}: MetricsControlsProps) {
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [dateRange, setDateRange] = useState<DateRange | undefined>({
    from: new Date(Date.now() - 24 * 60 * 60 * 1000),
    to: new Date(),
  });
  const [hasChanges, setHasChanges] = useState(false);

  // Apply button handler
  const handleApplyDateRange = () => {
      if (dateRange?.from && dateRange?.to && onDateRangeChange) {
        onDateRangeChange(dateRange.from, dateRange.to);
        setHasChanges(false);
      }
    };

    const toggleDatePicker = () => {
      setShowDatePicker(prev => !prev);
    };

  return (
    <div className="bg-white p-4 rounded-lg shadow">
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-[var(--text-secondary)]">
            期間:
          </span>
          
          {showDatePicker ? (
            <div className="flex items-center gap-2">
              <DatePickerWithRange 
                date={dateRange} 
                setDate={setDateRange}
              />
                <Button 
                  variant="default" 
                  size="sm" 
                  onClick={handleApplyDateRange}
                  className="text-xs"
                >
                  適用
                </Button>
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={toggleDatePicker}
                className="text-xs"
              >
                簡易選択に戻る
              </Button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
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
              <Button 
                variant="outline" 
                size="sm" 
                onClick={toggleDatePicker}
                className="text-xs flex items-center gap-1"
              >
                <Calendar className="h-3 w-3" />
                詳細選択
              </Button>
            </div>
          )}
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
    </div>
  );
}