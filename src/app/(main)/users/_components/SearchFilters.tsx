"use client";

import { Input } from "@/components/ui/input";
import { Search } from "lucide-react";
import { useEffect, useState } from "react";

interface SearchFiltersProps {
  onSearch: (
    query: string,
    status: string,
    role: string,
    customer: string
  ) => void;
  customers: Array<{ id: string; name: string }>;
  userRole: string;
}

export default function SearchFilters({
  onSearch,
  customers,
  userRole,
}: SearchFiltersProps) {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("すべて");
  const [role, setRole] = useState("すべて");
  const [customer, setCustomer] = useState("すべて");

  useEffect(() => {
    const delayDebounce = setTimeout(() => {
      onSearch(query.trim(), status, role, customer);
    }, 300);

    return () => clearTimeout(delayDebounce);
  }, [onSearch, query, status, role, customer]);

  return (
    <div
      className={`w-full ${userRole === "ADMIN" ? "max-w-[900px]" : "max-w-[600px]"} border border-gray-400 rounded-md px-4 py-3  bg-white overflow-hidden`}
    >
      <div className="flex items-center gap-6 flex-wrap">
        <div className="flex flex-1 flex-col items-start gap-1">
          <label className="text-gray-800 text-sm whitespace-nowrap">
            状態
          </label>

          {/* Select Box */}
          <div className="w-full">
            <select
              className="w-full min-w-20 bg-white border border-gray-400 rounded-lg px-3 py-1 text-sm text-gray-700 focus:outline-none focus:ring-1 focus:ring-gray-500 cursor-pointer"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
            >
              <option>すべて</option>
              <option value={"active"}>アクティブ</option>
              <option value={"inactive"}>非アクティブ</option>
            </select>
            {/* Right-pointing triangle icon */}
          </div>
        </div>
        {userRole === "ADMIN" && (
          <>
            <div className="flex flex-1 flex-col items-start gap-1">
              <label className="text-gray-800 text-sm whitespace-nowrap">
                権限
              </label>
              <div className="w-full">
                <select
                  className="w-full min-w-20 bg-white border border-gray-400 rounded-lg px-3 py-1 text-sm text-gray-700 focus:outline-none focus:ring-1 focus:ring-gray-500 cursor-pointer "
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                >
                  <option>すべて</option>
                  <option value={"ADMIN"}>システム管理者</option>
                  <option value={"CUSTOMER_ADMIN"}>顧客</option>
                </select>
              </div>
            </div>
            <div className="flex flex-1 flex-col items-start gap-1">
              <label className="text-gray-800 text-sm whitespace-nowrap">
                顧客
              </label>
              <div className="w-full">
                <select
                  className="w-full min-w-20 bg-white border border-gray-400 rounded-lg px-3 py-1 text-sm text-gray-700 focus:outline-none focus:ring-1 focus:ring-gray-500 cursor-pointer"
                  value={customer}
                  onChange={(e) => setCustomer(e.target.value)}
                >
                  <option>すべて</option>
                  {customers.map((c) => (
                    <option key={c.id} value={c.name}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </>
        )}

        {/* Input Box */}
        <div className="relative flex-1 min-w-[160px]">
          <Input
            placeholder="ユーザーを検索…"
            className="h-[30px] w-full bg-white border border-gray-400 rounded-full pr-12 pl-3 py-1 text-sm text-gray-700 focus:outline-none focus:ring-1 focus:ring-gray-500"
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
