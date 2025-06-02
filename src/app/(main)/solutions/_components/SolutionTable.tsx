"use client";

import { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
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
  const [sortKey, setSortKey] = useState<SortKey>("name");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");
  const router = useRouter();

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
      <ChevronUp size={16} />
    ) : (
      <ChevronDown size={16} />
    );
  };

  const handleViewDetails = (solutionId: string) => {
    router.push(`/solutions/${solutionId}`);
  };

  return (
    <div className="overflow-x-auto rounded-lg border border-[#BDC3C7]">
      <table className="w-full min-w-[900px]">
        <colgroup>
          <col className="w-1/10" />
          <col className="w-1/5" />
          <col className="w-1/5" />
          <col className="w-1/5" />
          <col className="w-1/10" />
        </colgroup>
        <thead className="bg-[#ECF0F1] border-b border-[#BDC3C7]">
          <tr>
            <th
              onClick={() => handleSort("name")}
              className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50] cursor-pointer"
            >
              <div className="flex justify-center items-center gap-1 select-none">
                <span>名前</span>
                {renderSortIndicator("name")}
              </div>
            </th>
            <th
              onClick={() => handleSort("version")}
              className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50] cursor-pointer"
            >
              <div className="flex justify-center items-center gap-1 select-none">
                <span>バージョン</span>
                {renderSortIndicator("version")}
              </div>
            </th>
            <th
              onClick={() => handleSort("compatibility")}
              className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50] cursor-pointer"
            >
              <div className="flex justify-center items-center gap-1 select-none">
                <span>互換デバイス</span>
                {renderSortIndicator("compatibility")}
              </div>
            </th>
            <th
              onClick={() => handleSort("status")}
              className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50] cursor-pointer"
            >
              <div className="flex justify-center items-center gap-1 select-none">
                <span>ステータス</span>
                {renderSortIndicator("status")}
              </div>
            </th>
            <th
              onClick={() => handleSort("installCount")}
              className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50] cursor-pointer"
            >
              <div className="flex justify-center items-center gap-1 select-none">
                <span>導入数</span>
                {renderSortIndicator("installCount")}
              </div>
            </th>
            <th className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50]">
              アクション
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-[#BDC3C7]">
          {sortedSolutions.length > 0 ? (
            sortedSolutions.map((solution) => (
              <tr
                key={solution.solution_id}
                className="border-t cursor-pointer hover:bg-[#F9F9F9] transition-colors duration-150 bg-white"
                onClick={() => handleViewDetails(solution.solution_id)}
              >
                <td className="px-6 py-3 text-sm text-[#2C3E50] max-w-0">
                  <div className="truncate">{solution.name}</div>
                </td>
                <td className="px-6 py-3 text-sm text-[#2C3E50] text-center whitespace-nowrap">
                  {solution.version}
                </td>
                <td className="px-6 py-3 text-sm text-[#2C3E50] text-center">
                  <div className="truncate">
                    {solution.compatibility.map(formatDeviceType).join(", ")}
                  </div>
                </td>
                <td className="px-6 py-3 text-sm text-center">
                  <SolutionStatusBadge status={solution.status} />
                </td>
                <td className="px-6 py-3 text-sm text-[#2C3E50] text-center whitespace-nowrap">
                  {solution.customers_count || 0} 顧客 /{" "}
                  {solution.devices_count || 0} デバイス
                </td>
                <td className="px-6 py-3 text-sm text-[#2C3E50] text-center">
                  <span className="px-2 py-1">-</span>
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
