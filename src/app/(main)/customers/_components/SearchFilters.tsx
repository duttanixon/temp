"use client";

import { Input } from "@/components/ui/input";
import { Search } from "lucide-react";
import { useEffect, useState } from "react";

interface SearchFiltersProps {
  onSearch: (query: string, status: string) => void;
}

export default function SearchFilters({ onSearch }: SearchFiltersProps) {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("すべて");

  useEffect(() => {
    const delayDebounce = setTimeout(() => {
      onSearch(query.trim(), status);
    }, 300);

    return () => clearTimeout(delayDebounce);
  }, [onSearch, query, status]);

  return (
    <div className="inline-block border border-gray-400 rounded-md px-4 py-3 bg-white overflow-hidden">
      <div className="flex items-center gap-6 flex-wrap">
        <div className="flex items-center gap-2">
          <label className="text-gray-800 text-sm whitespace-nowrap">
            状態:
          </label>
          <div className="w-40">
            <select
              className="w-full min-w-20 bg-white border border-gray-400 rounded-lg px-3 py-1 text-sm text-gray-700 focus:outline-none focus:ring-1 focus:ring-gray-500 cursor-pointer "
              value={status}
              onChange={(e) => setStatus(e.target.value)}
            >
              <option>すべて</option>
              <option value={"active"}>アクティブ</option>
              <option value={"inactive"}>非アクティブ</option>
            </select>
          </div>
        </div>

        <div className="relative min-w-[150px]">
          <Input
            placeholder="顧客を検索…"
            className="h-[30px] w-full bg-white border border-gray-400 rounded-full pr-12 pl-3 py-1 text-sm text-gray-700 focus:outline-none focus:ring-1 focus:ring-gray-500"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <div className="absolute inset-y-0 right-3 flex items-center pointer-events-none">
            <Search color="gray" />
          </div>
        </div>
      </div>
    </div>
  );
}
