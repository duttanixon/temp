"use client";

import { CustomerAssignment } from "@/types/customerSolution";
import { formatDeviceType } from "@/utils/solutions/solutionHelpers";
import { ChevronDown, ChevronUp } from "lucide-react";
import { useMemo, useState } from "react";

type CustomerSolutionTableProps = {
  initialSolutions: CustomerAssignment[];
};

type SortKey =
  | "solution_name"
  | "solution_version"
  | "license_status"
  | "compatibility"
  | "devices_count";
type SortDirection = "asc" | "desc";

export default function CustomerSolutionTable({
  initialSolutions,
}: CustomerSolutionTableProps) {
  // const [solutions] = useState<CustomerAssignment[]>(initialSolutions);
  const [sortKey, setSortKey] = useState<SortKey>("solution_name");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");

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
        case "solution_name":
          valA = a.solution_name || "";
          valB = b.solution_name || "";
          break;
        case "solution_version":
          valA = a.solution_version || "";
          valB = b.solution_version || "";
          break;
        case "license_status":
          valA = a.license_status || "";
          valB = b.license_status || "";
          break;
        case "compatibility":
          valA = a.compatibility?.map(formatDeviceType).join(", ") || "";
          valB = b.compatibility?.map(formatDeviceType).join(", ") || "";
          break;
        case "devices_count":
          valA = a.devices_count || 0;
          valB = b.devices_count || 0;
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

  const renderSortIcon = (key: SortKey) => {
    if (key !== sortKey) return null;
    return sortDirection === "asc" ? (
      <ChevronUp className="w-4 h-4 ml-1 inline" />
    ) : (
      <ChevronDown className="w-4 h-4 ml-1 inline" />
    );
  };

  return (
    <div className="overflow-x-auto rounded-lg border border-[#BDC3C7]">
      <table className="w-full min-w-[800px]">
        <colgroup>
          <col className="w-1/5" />
          <col className="w-1/5" />
          <col className="w-1/5" />
          <col className="w-1/10" />
          <col className="w-1/5" />
          <col className="w-1/10" />
        </colgroup>
        <thead className="bg-[#ECF0F1] border-b border-[#BDC3C7]">
          <tr>
            <th
              onClick={() => handleSort("solution_name")}
              className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50] cursor-pointer select-none"
            >
              <div className="flex justify-center items-center gap-1 select-none">
                <div className="flex flex-col items-center">
                  <div>ソリューション名</div>
                  <div className="text-xs text-[#7F8C8D]">Solution Name</div>
                </div>
                {renderSortIcon("solution_name")}
              </div>
            </th>
            <th
              onClick={() => handleSort("solution_version")}
              className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50] cursor-pointer select-none"
            >
              <div className="flex justify-center items-center gap-1 select-none">
                <div className="flex flex-col items-center">
                  <div>バージョン</div>
                  <div className="text-xs text-[#7F8C8D]">Version</div>
                </div>
                {renderSortIcon("solution_version")}
              </div>
            </th>
            <th
              onClick={() => handleSort("compatibility")}
              className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50] cursor-pointer select-none"
            >
              <div className="flex justify-center items-center gap-1 select-none">
                <div className="flex flex-col items-center">
                  <div>互換デバイス</div>
                  <div className="text-xs text-[#7F8C8D]">Compatibility</div>
                </div>
                {renderSortIcon("compatibility")}
              </div>
            </th>
            <th
              onClick={() => handleSort("license_status")}
              className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50] cursor-pointer select-none"
            >
              <div className="flex justify-center items-center gap-1 select-none">
                <div className="flex flex-col items-center">
                  <div>ステータス</div>
                  <div className="text-xs text-[#7F8C8D]">Status</div>
                </div>
                {renderSortIcon("license_status")}
              </div>
            </th>
            <th
              onClick={() => handleSort("devices_count")}
              className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50] cursor-pointer select-none"
            >
              <div className="flex justify-center items-center gap-1 select-none">
                <div className="flex flex-col items-center">
                  <div>導入数</div>
                  <div className="text-xs text-[#7F8C8D]">Devices Count</div>
                </div>
                {renderSortIcon("devices_count")}
              </div>
            </th>
            <th className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50]">
              <div className="flex flex-col items-center">
                <div>アクション</div>
                <div className="text-xs text-[#7F8C8D]">Actions</div>
              </div>
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-[#BDC3C7]">
          {sortedSolutions.length > 0 ? (
            sortedSolutions.map((solution) => (
              <tr key={solution.solution_id} className="hover:bg-[#F8F9FA]">
                {/* 名前 */}
                <td className="px-6 py-3 text-sm text-[#2C3E50] max-w-0">
                  <div className="truncate">{solution.solution_name}</div>
                </td>
                {/* バージョン */}
                <td className="px-6 py-3 whitespace-nowrap text-sm text-[#2C3E50] text-center">
                  {solution.solution_version}
                </td>
                {/* 互換デバイス */}
                <td className="px-6 py-3 whitespace-nowrap text-sm text-[#2C3E50] text-center">
                  {solution.compatibility ? (
                    solution.compatibility
                      .map((device) => formatDeviceType(device))
                      .join(", ")
                  ) : (
                    <span>-</span>
                  )}
                </td>
                {/* ライセンスステータス */}
                <td className="px-6 py-3 whitespace-nowrap text-sm text-[#2C3E50] text-center">
                  <span
                    className={`px-2 py-1 rounded-full ${
                      solution.license_status === "ACTIVE"
                        ? "bg-green-100 text-green-700"
                        : solution.license_status === "SUSPENDED"
                          ? "bg-yellow-100 text-yellow-700"
                          : "bg-gray-100 text-gray-700"
                    }`}
                  >
                    {solution.license_status === "ACTIVE"
                      ? "アクティブ"
                      : solution.license_status === "SUSPENDED"
                        ? "一時停止中"
                        : "期限切れ"}
                  </span>
                </td>
                {/* 導入数 */}
                <td className="px-6 py-3 whitespace-nowrap text-sm text-[#2C3E50] text-center">
                  <span className="px-2 py-1">
                    {solution.devices_count || 0} デバイス
                  </span>
                </td>
                {/* アクション */}
                <td className="px-6 py-3 whitespace-nowrap text-sm text-[#2C3E50] text-center">
                  <span className="px-2 py-1 ">-</span>
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
