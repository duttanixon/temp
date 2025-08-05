"use client";

import { useGetCustomer } from "@/app/(main)/_components/_hooks/useGetCustomer";
import { useGetSolution } from "@/app/(main)/_components/_hooks/useGetSolution";
import { Input } from "@/components/ui/input";
import { Search } from "lucide-react";
import { useSession } from "next-auth/react";

type Props = {
  deviceType: string;
  setDeviceType: (val: string) => void;
  customerId: string;
  setCustomerId: (val: string) => void;
  solutionName: string;
  setSolutionName: (val: string) => void;
  query: string;
  setQuery: (val: string) => void;
};

export default function DeviceFilters({
  deviceType,
  setDeviceType,
  customerId,
  setCustomerId,
  solutionName,
  setSolutionName,
  query,
  setQuery,
}: Props) {
  const { data: session } = useSession();
  console.log("Session:", session);
  const role = session?.user?.role;
  const { customer: customers, isLoading: isLoadingCustomers } =
    useGetCustomer();
  const { solution: solutions, isLoading: isLoadingSolutions } =
    useGetSolution();

  return (
    <div className="inline-block border border-gray-400 rounded-md px-4 py-3 bg-white overflow-hidden">
      <div className="flex items-end gap-6 flex-wrap">
        <div className="flex flex-col flex-1 items-start gap-1">
          <label className="text-gray-800 text-sm whitespace-nowrap">
            タイプ
          </label>
          <div className="w-full sm:w-40">
            <select
              value={deviceType}
              onChange={(e) => setDeviceType(e.target.value)}
              className="w-full min-w-20 bg-white border border-gray-400 rounded-lg px-3 py-1 text-sm text-gray-700 cursor-pointer"
            >
              <option value="">すべて</option>
              <option value="NVIDIA_JETSON">NVIDIA Jetson</option>
              <option value="RASPBERRY_PI">Raspberry Pi</option>
            </select>
          </div>
        </div>
        {(role === "ADMIN" || role === "ENGINEER") && (
          <div className="flex flex-col flex-1 items-start gap-1">
            <label className="text-gray-800 text-sm whitespace-nowrap">
              顧客
            </label>
            <div className="w-full sm:w-40">
              <select
                value={customerId}
                onChange={(e) => setCustomerId(e.target.value)}
                className="w-full min-w-20 bg-white border border-gray-400 rounded-lg px-3 py-1 text-sm text-gray-700 cursor-pointer "
                disabled={isLoadingCustomers}
              >
                <option value="">すべて</option>
                {customers?.map((c) => (
                  <option key={c.customer_id} value={c.customer_id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        )}
        <div className="flex flex-col flex-1 items-start gap-1">
          <label className="text-gray-800 text-sm whitespace-nowrap">
            ソリューション
          </label>
          <div className="w-full sm:w-40">
            <select
              value={solutionName}
              onChange={(e) => setSolutionName(e.target.value)}
              className="w-full min-w-20 bg-white border border-gray-400 rounded-lg px-3 py-1 text-sm text-gray-700 cursor-pointer "
              disabled={isLoadingSolutions}
            >
              <option value="">すべて</option>
              {solutions?.map((s) => (
                <option key={s.name} value={s.name}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className="relative">
          <Input
            placeholder="デバイスを検索…"
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
