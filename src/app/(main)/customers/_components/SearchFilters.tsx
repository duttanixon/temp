"use client";

import { useEffect, useState } from "react";
import { Input } from "@/components/ui/input";

interface SearchFiltersProps {
  onSearch: (query: string, status: string) => void;
}

export default function SearchFilters({ onSearch }: SearchFiltersProps) {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("全ての状態");

  useEffect(() => {
    const delayDebounce = setTimeout(() => {
      onSearch(query.trim(), status);
    }, 300); // debounce

    return () => clearTimeout(delayDebounce);
  }, [query, status, onSearch]);

  return (
    <div className="border border-gray-400 rounded-md px-4 py-3 w-2/5">
      <div className="flex items-center gap-10">
        {" "}
        {/* increased gap from 4 to 10 */}
        <label className="text-gray-800 text-sm">状態:</label>
        <div className="relative">
          <select
            className="appearance-none border border-gray-400 rounded-full px-3 py-1 text-sm text-gray-700 pr-8 focus:outline-none focus:ring-1 focus:ring-gray-500"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
          >
            <option>全ての状態</option>
            <option>Active</option>
            <option>Inactive</option>
          </select>
          <div className="pointer-events-none absolute inset-y-0 right-2 flex items-center">
            <svg
              className="w-4 h-4 text-gray-600"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path d="M5.23 7.21a.75.75 0 0 1 1.06.02L10 10.94l3.71-3.71a.75.75 0 0 1 1.08 1.04l-4.25 4.25a.75.75 0 0 1-1.08 0L5.21 8.27a.75.75 0 0 1 .02-1.06z" />
            </svg>
          </div>
        </div>
        <div className="relative">
          <Input
            placeholder="顧客を検索…"
            className="w-64 border border-gray-400 rounded-full pr-10 pl-3 py-1 text-sm text-gray-700 focus:outline-none focus:ring-1 focus:ring-gray-500"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <div className="absolute inset-y-0 right-3 flex items-center pointer-events-none">
            <svg
              className="w-4 h-4 text-gray-500"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M12.9 14.32a8 8 0 1 1 1.414-1.414l4.387 4.387a1 1 0 0 1-1.414 1.414l-4.387-4.387zM10 16a6 6 0 1 0 0-12 6 6 0 0 0 0 12z"
                clipRule="evenodd"
              />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}
