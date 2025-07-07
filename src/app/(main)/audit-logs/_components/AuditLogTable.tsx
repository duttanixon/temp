"use client";

import { AuditLog } from "@/types/auditLog";
import { auditLogService } from "@/services/auditLogService";
import { format } from "date-fns";
import { ja } from "date-fns/locale";

interface AuditLogTableProps {
  logs: AuditLog[];
}

export default function AuditLogTable({ logs }: AuditLogTableProps) {
  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), "yyyy/MM/dd HH:mm:ss", {
        locale: ja,
      });
    } catch {
      return dateString;
    }
  };

  const formatDetails = (details: Record<string, any> | null) => {
    if (!details) return "-";

    // Extract important fields from details
    const importantKeys = [
      "changed_fields",
      "reason",
      "error",
      "old_value",
      "new_value",
    ];
    const relevantDetails = importantKeys
      .filter((key) => details[key])
      .map((key) => `${key}: ${JSON.stringify(details[key])}`)
      .join(", ");

    return relevantDetails || JSON.stringify(details).slice(0, 100) + "...";
  };

  if (logs.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        監査ログが見つかりませんでした
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              タイムスタンプ
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              アクション
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              ユーザー
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              リソース
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              IPアドレス
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              詳細
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {logs.map((log) => (
            <tr key={log.log_id} className="hover:bg-gray-50">
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {formatDate(log.timestamp)}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm">
                <span
                  className={auditLogService.getActionTypeColor(
                    log.action_type
                  )}
                >
                  {auditLogService.formatActionType(log.action_type)}
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                <div>
                  <div className="font-medium">
                    {log.user_email || "System"}
                  </div>
                  {log.user_name && (
                    <div className="text-xs text-gray-500">{log.user_name}</div>
                  )}
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                <div>
                  <div>
                    {auditLogService.formatResourceType(log.resource_type)}
                  </div>
                  {log.resource_id && (
                    <div className="text-xs text-gray-500">
                      {log.resource_id}
                    </div>
                  )}
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {log.ip_address || "-"}
              </td>
              <td
                className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate"
                title={JSON.stringify(log.details)}
              >
                {formatDetails(log.details)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
