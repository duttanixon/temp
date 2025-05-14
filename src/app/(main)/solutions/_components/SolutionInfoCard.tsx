import { formatDistanceToNow } from "date-fns";
import { ja } from "date-fns/locale";
import { Solution } from "@/types/solution";
import SolutionStatusBadge from "./SolutionStatusBadge";
import { formatDeviceType } from "@/utils/solutions/solutionHelpers";

type SolutionInfoCardProps = {
  solution: Solution;
};

export default function SolutionInfoCard({ solution }: SolutionInfoCardProps) {
  return (
    <div className="bg-white rounded-lg border border-[#BDC3C7] overflow-hidden">
      <div className="px-6 py-4 border-b border-[#BDC3C7]">
        <h2 className="text-lg font-semibold text-[#2C3E50]">ソリューション情報</h2>
      </div>

      <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-4">
          <div>
            <h3 className="text-sm font-medium text-[#7F8C8D]">基本情報</h3>
            <div className="mt-2 space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-[#7F8C8D]">名前</span>
                <span className="text-sm font-medium text-[#2C3E50]">
                  {solution.name}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-[#7F8C8D]">バージョン</span>
                <span className="text-sm font-medium text-[#2C3E50]">
                  {solution.version}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-[#7F8C8D]">ステータス</span>
                <span className="text-sm font-medium text-[#2C3E50]">
                  <SolutionStatusBadge status={solution.status} />
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-[#7F8C8D]">互換デバイス</span>
                <span className="text-sm font-medium text-[#2C3E50]">
                  {solution.compatibility
                    .map((device) => formatDeviceType(device))
                    .join(", ")}
                </span>
              </div>
            </div>
          </div>

          <div>
            <h3 className="text-sm font-medium text-[#7F8C8D]">
              説明
            </h3>
            <div className="mt-2 p-3 bg-gray-50 rounded-md text-sm text-[#2C3E50]">
              {solution.description || "説明はありません。"}
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <h3 className="text-sm font-medium text-[#7F8C8D]">利用状況</h3>
            <div className="mt-2 space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-[#7F8C8D]">導入顧客数</span>
                <span className="text-sm font-medium text-[#2C3E50]">
                  {solution.customers_count || 0}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-[#7F8C8D]">導入デバイス数</span>
                <span className="text-sm font-medium text-[#2C3E50]">
                  {solution.devices_count || 0}
                </span>
              </div>
            </div>
          </div>

          <div>
            <h3 className="text-sm font-medium text-[#7F8C8D]">登録情報</h3>
            <div className="mt-2 space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-[#7F8C8D]">作成日</span>
                <span className="text-sm font-medium text-[#2C3E50]">
                  {new Date(solution.created_at).toLocaleDateString("ja-JP")}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-[#7F8C8D]">最終更新</span>
                <span className="text-sm font-medium text-[#2C3E50]">
                  {solution.updated_at
                    ? new Date(solution.updated_at).toLocaleDateString("ja-JP")
                    : "-"}
                </span>
              </div>
            </div>
          </div>

          {solution.configuration_template && (
            <div>
              <h3 className="text-sm font-medium text-[#7F8C8D]">設定テンプレート</h3>
              <div className="mt-2 p-3 bg-gray-50 rounded-md overflow-auto max-h-48">
                <pre className="text-xs text-[#2C3E50]">
                  {JSON.stringify(solution.configuration_template, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}