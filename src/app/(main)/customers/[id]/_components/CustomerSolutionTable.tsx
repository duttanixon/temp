"use client";

import { CustomerAssignment } from "@/types/customerSolution";
import { formatDeviceType } from "@/utils/solutions/solutionHelpers";
import { useState } from "react";

type CustomerSolutionTableProps = {
  initialSolutions: CustomerAssignment[];
};

export default function CustomerSolutionTable({
  initialSolutions,
}: CustomerSolutionTableProps) {
  const [solutions] = useState<CustomerAssignment[]>(initialSolutions);

  return (
    <div className="overflow-x-auto rounded-lg border border-[#BDC3C7]">
      <table className="w-full min-w-[800px]">
        <colgroup>
          <col className="w-1/5" /> {/* 名前 */}
          <col className="w-1/5" /> {/* バージョン */}
          <col className="w-1/5" /> {/* 互換デバイス */}
          <col className="w-1/10" /> {/* ライセンスステータス */}
          <col className="w-1/5" /> {/* 導入数 */}
          <col className="w-1/10" /> {/* アクション */}
        </colgroup>
        <thead className="bg-[#ECF0F1] border-b border-[#BDC3C7]">
          <tr>
            <th
              scope="col"
              className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50]">
              名前
            </th>
            <th
              scope="col"
              className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50]">
              バージョン
            </th>
            <th
              scope="col"
              className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50]">
              互換デバイス
            </th>
            <th
              scope="col"
              className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50]">
              ステータス
            </th>
            <th
              scope="col"
              className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50]">
              導入数
            </th>
            <th
              scope="col"
              className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50]">
              アクション
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-[#BDC3C7]">
          {solutions.length > 0 ? (
            solutions.map((solution) => (
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
                    }`}>
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
                className="px-6 py-4 text-center text-sm text-[#7F8C8D]">
                ソリューションが見つかりません
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
