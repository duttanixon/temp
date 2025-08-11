"use client";

import { Search, RefreshCw, Filter } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface PackageFiltersProps {
  searchQuery: string;
  onSearchChange: (query: string) => void;
  sortBy: "name" | "version" | "date";
  onSortChange: (sort: "name" | "version" | "date") => void;
  onRefresh: () => void;
  totalCount: number;
}

/**
 * Filter controls for package list
 * Follows Interface Segregation - provides only necessary filter options
 */
export default function PackageFilters({
  searchQuery,
  onSearchChange,
  sortBy,
  onSortChange,
  onRefresh,
  totalCount,
}: PackageFiltersProps) {
  return (
    <div className="flex flex-col sm:flex-row gap-3 items-center justify-between">
      <div className="flex flex-1 gap-3 w-full sm:w-auto">
        {/* Search Input */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#7F8C8D]" />
          <Input
            type="text"
            placeholder="Search packages..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* Sort Dropdown */}
        <Select value={sortBy} onValueChange={onSortChange}>
          <SelectTrigger className="w-[180px]">
            <Filter className="h-4 w-4 mr-2" />
            <SelectValue placeholder="Sort by" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="date">Latest First</SelectItem>
            <SelectItem value="name">Name (A-Z)</SelectItem>
            <SelectItem value="version">Version</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="flex items-center gap-3">
        {/* Results Count */}
        <span className="text-sm text-[#7F8C8D]">
          {totalCount} package{totalCount !== 1 ? "s" : ""} found
        </span>

        {/* Refresh Button */}
        <Button
          variant="outline"
          size="sm"
          onClick={onRefresh}
          className="gap-2"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh
        </Button>
      </div>
    </div>
  );
}
