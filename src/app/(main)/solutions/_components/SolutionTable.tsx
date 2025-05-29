"use client";

import { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
// import { formatDistanceToNow } from "date-fns";
// import { ja } from "date-fns/locale";
import { Solution } from "@/types/solution";
import SolutionStatusBadge from "./SolutionStatusBadge";
import { formatDeviceType } from "@/utils/solutions/solutionHelpers";
import { ChevronDown, ChevronUp } from "lucide-react";

type SolutionTableProps = {
  initialSolutions: Solution[];
};

type SortKey = "name" | "version" | "compatibility" | "status" | "installCount";
type SortDirection = "asc" | "desc";

export default function SolutionTable({
  initialSolutions,
}: SolutionTableProps) {
  // const [solutions] = useState<Solution[]>(initialSolutions);
  const [sortKey, setSortKey] = useState<SortKey>("name");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");
  const router = useRouter();

  const handleViewDetails = (solutionId: string) => {
    router.push(`/solutions/${solutionId}`);
  };

  const handleSort = (key: SortKey) => {
    if (key === sortKey) {
      setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDirection("asc");
    }
  };

  const sortedSolutions = useMemo(() => {
    return [...initialSolutions].sort((a, b) => {
      let valA: string | number = "";
      let valB: string | number = "";

      switch (sortKey) {
        case "name":
          valA = a.name || "";
          valB = b.name || "";
          break;
        case "version":
          valA = a.version || "";
          valB = b.version || "";
          break;
        case "compatibility":
          valA = a.compatibility.map(formatDeviceType).join(", ");
          valB = b.compatibility.map(formatDeviceType).join(", ");
          break;
        case "status":
          valA = a.status || "";
          valB = b.status || "";
          break;
        case "installCount":
          valA = (a.customers_count || 0) + (a.devices_count || 0);
          valB = (b.customers_count || 0) + (b.devices_count || 0);
          break;
      }

      if (typeof valA === "string") {
        valA = valA.toLowerCase();
        valB = (valB as string).toLowerCase();
      }

      if (valA < valB) return sortDirection === "asc" ? -1 : 1;
      if (valA > valB) return sortDirection === "asc" ? 1 : -1;
      return 0;
    });
  }, [initialSolutions, sortKey, sortDirection]);

  const renderSortIndicator = (key: SortKey) => {
    if (key !== sortKey) return null;
    return sortDirection === "asc" ? (
      <ChevronUp className="inline w-4 h-4 ml-1" />
    ) : (
      <ChevronDown className="inline w-4 h-4 ml-1" />
    );
  };

  return (
    <div className="overflow-x-auto rounded-lg border border-[#BDC3C7]">
      <table className="min-w-full divide-y divide-[#BDC3C7]">
        <thead className="bg-[#ECF0F1]">
          <tr>
            <th
              onClick={() => handleSort("name")}
              className="px-6 py-3 text-left text-sm font-semibold text-[#2C3E50] cursor-pointer select-none"
            >
              <div className="flex items-center">
                名前{renderSortIndicator("name")}
              </div>
            </th>
            <th
              onClick={() => handleSort("version")}
              className="px-6 py-3 text-left text-sm font-semibold text-[#2C3E50] cursor-pointer select-none"
            >
              <div className="flex items-center">
                バージョン{renderSortIndicator("version")}
              </div>
            </th>
            <th
              onClick={() => handleSort("compatibility")}
              className="px-6 py-3 text-left text-sm font-semibold text-[#2C3E50] cursor-pointer select-none"
            >
              <div className="flex items-center">
                互換デバイス{renderSortIndicator("compatibility")}
              </div>
            </th>
            <th
              onClick={() => handleSort("status")}
              className="px-6 py-3 text-left text-sm font-semibold text-[#2C3E50] cursor-pointer select-none"
            >
              <div className="flex items-center">
                ステータス{renderSortIndicator("status")}
              </div>
            </th>
            <th
              onClick={() => handleSort("installCount")}
              className="px-6 py-3 text-left text-sm font-semibold text-[#2C3E50] cursor-pointer select-none"
            >
              <div className="flex items-center">
                導入数{renderSortIndicator("installCount")}
              </div>
            </th>
            <th className="px-6 py-3 text-right text-sm font-semibold text-[#2C3E50]">
              アクション
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-[#BDC3C7]">
          {sortedSolutions.length > 0 ? (
            sortedSolutions.map((solution) => (
              <tr key={solution.solution_id} className="hover:bg-[#F8F9FA]">
                <td className="px-6 py-4 whitespace-nowrap text-sm text-[#2C3E50]">
                  {solution.name}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-[#2C3E50]">
                  {solution.version}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-[#2C3E50]">
                  {solution.compatibility
                    .map((device) => formatDeviceType(device))
                    .join(", ")}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <SolutionStatusBadge status={solution.status} />
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-[#2C3E50]">
                  {solution.customers_count || 0} 顧客 /{" "}
                  {solution.devices_count || 0} デバイス
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                  <button
                    onClick={() => handleViewDetails(solution.solution_id)}
                    className="text-blue-600 hover:text-blue-800 font-medium"
                  >
                    詳細
                  </button>
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td
                colSpan={6}
                className="px-6 py-4 text-center text-sm text-[#7F8C8D]"
              >
                ソリューションが見つかりません
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
