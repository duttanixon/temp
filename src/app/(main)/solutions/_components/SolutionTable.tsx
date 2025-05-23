"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { formatDistanceToNow } from "date-fns";
import { ja } from "date-fns/locale";
import { Solution } from "@/types/solution";
import SolutionStatusBadge from "./SolutionStatusBadge";
import { formatDeviceType } from "@/utils/solutions/solutionHelpers";


type SolutionTableProps = {
    initialSolutions: Solution[];
  };

  
export default function SolutionTable({ initialSolutions }: SolutionTableProps) {
    const [solutions] = useState<Solution[]>(initialSolutions);
    const router = useRouter();

    const handleViewDetails = (solutionId: string) => {
        router.push(`/solutions/${solutionId}`);
      };
    
    return (
        <div className="overflow-x-auto rounded-lg border border-[#BDC3C7]">
            <table className="min-w-full divide-y divide-[#BDC3C7]">
                <thead className="bg-[#ECF0F1]">
                    <tr>
                        <th
                        scope="col"
                        className="px-6 py-3 text-left text-sm font-semibold text-[#2C3E50]"
                        >
                        名前
                        </th>
                        <th
                        scope="col"
                        className="px-6 py-3 text-left text-sm font-semibold text-[#2C3E50]"
                        >
                        バージョン
                        </th>
                        <th
                        scope="col"
                        className="px-6 py-3 text-left text-sm font-semibold text-[#2C3E50]"
                        >
                        互換デバイス
                        </th>
                        <th
                        scope="col"
                        className="px-6 py-3 text-left text-sm font-semibold text-[#2C3E50]"
                        >
                        ステータス
                        </th>
                        <th
                        scope="col"
                        className="px-6 py-3 text-left text-sm font-semibold text-[#2C3E50]"
                        >
                        導入数
                        </th>
                        <th
                        scope="col"
                        className="px-6 py-3 text-right text-sm font-semibold text-[#2C3E50]"
                        >
                        アクション
                        </th>
                    </tr>
                </thead>
                <tbody className="bg-white divide-y divide-[#BDC3C7]">
                    {solutions.length > 0 ? (
                        solutions.map((solution) => (
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
                            {solution.customers_count || 0} 顧客 / {solution.devices_count || 0} デバイス
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