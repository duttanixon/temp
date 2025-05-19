"use client";

import { useEffect, useState } from "react";
import { Input } from "@/components/ui/input";
import { Search } from "lucide-react";

interface SearchFiltersProps {
  onSearch: (query: string, status: string) => void;
}

export default function SearchFilters({ onSearch }: SearchFiltersProps) {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("全ての状態");

  useEffect(() => {
    const delayDebounce = setTimeout(() => {
      onSearch(query.trim(), status);
    }, 300);

    return () => clearTimeout(delayDebounce);
  }, [onSearch, query, status]);

  return (
    <div className="relative border border-gray-400 rounded-md px-4 py-3 w-2/5 bg-white overflow-hidden">
      <div className="flex items-center gap-6 flex-wrap">
        <label className="text-gray-800 text-sm whitespace-nowrap">状態:</label>

        {/* Select Box */}
        <div className="relative w-40">
          <select
            className="appearance-none w-full bg-white border border-gray-400 rounded-lg px-3 py-1 text-sm text-gray-700 pr-10 focus:outline-none focus:ring-1 focus:ring-gray-500"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
          >
            <option>全ての状態</option>
            <option value={"active"}>アクティブ</option>
            <option value={"inactive"}>非アクティブ</option>
          </select>
          {/* Right-pointing triangle icon */}
          <div className="pointer-events-none absolute inset-y-0 right-3 flex items-center">
            <svg
              className="w-5 h-5 text-gray-600"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <polygon points="8,5 16,12 8,19" />
            </svg>
          </div>
        </div>

        {/* Input Box */}
        <div className="relative flex-grow min-w-[150px]">
          <Input
            placeholder="顧客を検索…"
            className="w-full bg-white border border-gray-400 rounded-full pr-12 pl-3 py-1 text-sm text-gray-700 focus:outline-none focus:ring-1 focus:ring-gray-500"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          {/* No entry icon — flipped line */}
          <div className="absolute inset-y-0 right-3 flex items-center pointer-events-none">
            <Search color="gray" />
          </div>
        </div>
      </div>
    </div>
  );
}
