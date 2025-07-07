"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { format } from "date-fns";
import { ja } from "date-fns/locale";
import { CalendarIcon, Filter, X } from "lucide-react";
import { AuditLogFilter } from "@/types/auditLog";
import { cn } from "@/lib/utils";

interface AuditLogFiltersProps {
  filters: AuditLogFilter;
  actionTypes: string[];
  resourceTypes: string[];
  onFiltersChange: (filters: AuditLogFilter) => void;
  onReset: () => void;
}

export default function AuditLogFilters({
  filters,
  actionTypes,
  resourceTypes,
  onFiltersChange,
  onReset,
}: AuditLogFiltersProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const handleDateChange = (
    field: "start_date" | "end_date",
    date: Date | undefined
  ) => {
    if (date) {
      onFiltersChange({
        ...filters,
        [field]: format(date, "yyyy-MM-dd"),
      });
    } else {
      const { [field]: _, ...rest } = filters;
      onFiltersChange(rest);
    }
  };

  const formatActionTypeForDisplay = (actionType: string): string => {
    return actionType
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  const formatResourceTypeForDisplay = (resourceType: string): string => {
    return resourceType.charAt(0).toUpperCase() + resourceType.slice(1);
  };

  return (
    <div className="bg-white p-4 rounded-lg border space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4" />
          <h3 className="font-medium">フィルター</h3>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          {isExpanded ? "折りたたむ" : "展開"}
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Date Range */}
        <div className="space-y-2">
          <Label>開始日</Label>
          <Popover>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                className={cn(
                  "w-full justify-start text-left font-normal",
                  !filters.start_date && "text-muted-foreground"
                )}
              >
                <CalendarIcon className="mr-2 h-4 w-4" />
                {filters.start_date
                  ? format(new Date(filters.start_date), "yyyy/MM/dd", {
                      locale: ja,
                    })
                  : "選択してください"}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="start">
              <Calendar
                mode="single"
                selected={
                  filters.start_date ? new Date(filters.start_date) : undefined
                }
                onSelect={(date) => handleDateChange("start_date", date)}
                initialFocus
              />
            </PopoverContent>
          </Popover>
        </div>

        <div className="space-y-2">
          <Label>終了日</Label>
          <Popover>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                className={cn(
                  "w-full justify-start text-left font-normal",
                  !filters.end_date && "text-muted-foreground"
                )}
              >
                <CalendarIcon className="mr-2 h-4 w-4" />
                {filters.end_date
                  ? format(new Date(filters.end_date), "yyyy/MM/dd", {
                      locale: ja,
                    })
                  : "選択してください"}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="start">
              <Calendar
                mode="single"
                selected={
                  filters.end_date ? new Date(filters.end_date) : undefined
                }
                onSelect={(date) => handleDateChange("end_date", date)}
                initialFocus
              />
            </PopoverContent>
          </Popover>
        </div>

        {/* Action Type */}
        <div className="space-y-2">
          <Label>アクションタイプ</Label>
          <Select
            value={filters.action_type || ""}
            onValueChange={(value) =>
              onFiltersChange({
                ...filters,
                action_type: value || undefined,
              })
            }
          >
            <SelectTrigger>
              <SelectValue placeholder="すべて" />
            </SelectTrigger>
            <SelectContent>
              {/* <SelectItem value="">すべて</SelectItem> */}
              {actionTypes.map((type) => (
                <SelectItem key={type} value={type}>
                  {formatActionTypeForDisplay(type)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Resource Type */}
        <div className="space-y-2">
          <Label>リソースタイプ</Label>
          <Select
            value={filters.resource_type || ""}
            onValueChange={(value) =>
              onFiltersChange({
                ...filters,
                resource_type: value || undefined,
              })
            }
          >
            <SelectTrigger>
              <SelectValue placeholder="すべて" />
            </SelectTrigger>
            <SelectContent>
              {/* <SelectItem value="">すべて</SelectItem> */}
              {resourceTypes.map((type) => (
                <SelectItem key={type} value={type}>
                  {formatResourceTypeForDisplay(type)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {isExpanded && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pt-4 border-t">
          {/* User Email */}
          <div className="space-y-2">
            <Label>ユーザーメール</Label>
            <Input
              placeholder="メールアドレスを入力"
              value={filters.user_email || ""}
              onChange={(e) =>
                onFiltersChange({
                  ...filters,
                  user_email: e.target.value || undefined,
                })
              }
            />
          </div>

          {/* IP Address */}
          <div className="space-y-2">
            <Label>IPアドレス</Label>
            <Input
              placeholder="IPアドレスを入力"
              value={filters.ip_address || ""}
              onChange={(e) =>
                onFiltersChange({
                  ...filters,
                  ip_address: e.target.value || undefined,
                })
              }
            />
          </div>

          {/* Sort Options */}
          <div className="space-y-2">
            <Label>並び替え</Label>
            <div className="flex gap-2">
              <Select
                value={filters.sort_by || "timestamp"}
                onValueChange={(value) =>
                  onFiltersChange({
                    ...filters,
                    sort_by: value,
                  })
                }
              >
                <SelectTrigger className="flex-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="timestamp">タイムスタンプ</SelectItem>
                  <SelectItem value="action_type">アクションタイプ</SelectItem>
                  <SelectItem value="resource_type">リソースタイプ</SelectItem>
                  <SelectItem value="user_email">ユーザー</SelectItem>
                </SelectContent>
              </Select>
              <Select
                value={filters.sort_order || "desc"}
                onValueChange={(value) =>
                  onFiltersChange({
                    ...filters,
                    sort_order: value as "asc" | "desc",
                  })
                }
              >
                <SelectTrigger className="w-24">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="desc">降順</SelectItem>
                  <SelectItem value="asc">昇順</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>
      )}

      <div className="flex justify-end gap-2">
        <Button variant="outline" size="sm" onClick={onReset}>
          <X className="w-4 h-4 mr-1" />
          リセット
        </Button>
      </div>
    </div>
  );
}
