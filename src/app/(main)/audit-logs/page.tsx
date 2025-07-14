"use client";

import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Download, RefreshCw } from "lucide-react";
import { auditLogService } from "@/services/auditLogService";
import { AuditLog, AuditLogFilter } from "@/types/auditLog";
import AuditLogTable from "./_components/AuditLogTable";
import AuditLogFilters from "./_components/AuditLogFilters";
import UserPagination from "../users/_components/Pagination";
import { toast } from "sonner";

export default function AuditLogsPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [totalLogs, setTotalLogs] = useState(0);
  const [page, setPage] = useState(0);
  const [actionTypes, setActionTypes] = useState<string[]>([]);
  const [resourceTypes, setResourceTypes] = useState<string[]>([]);

  const itemsPerPage = 50;

  const [filters, setFilters] = useState<AuditLogFilter>({
    skip: 0,
    limit: itemsPerPage,
    sort_by: "timestamp",
    sort_order: "desc",
  });

  // Fetch action and resource types
  useEffect(() => {
    const fetchTypes = async () => {
      try {
        const [actions, resources] = await Promise.all([
          auditLogService.getActionTypes(),
          auditLogService.getResourceTypes(),
        ]);
        setActionTypes(actions);
        setResourceTypes(resources);
      } catch (error) {
        console.error("Failed to fetch types:", error);
      }
    };
    fetchTypes();
  }, []);

  // Fetch audit logs
  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      const response = await auditLogService.getAuditLogs({
        ...filters,
        skip: page * itemsPerPage,
        limit: itemsPerPage,
      });
      setLogs(response.logs);
      setTotalLogs(response.total);
    } catch (error) {
      console.error("Failed to fetch audit logs:", error);
      toast.error("監査ログの取得に失敗しました。");
    } finally {
      setLoading(false);
    }
  }, [filters, page]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  const handleFiltersChange = (newFilters: AuditLogFilter) => {
    setFilters(newFilters);
    setPage(0); // Reset to first page when filters change
  };

  const handleReset = () => {
    setFilters({
      skip: 0,
      limit: itemsPerPage,
      sort_by: "timestamp",
      sort_order: "desc",
    });
    setPage(0);
  };

  const handleExport = async (format: "csv" | "json") => {
    setExporting(true);
    try {
      const blob = await auditLogService.exportAuditLogs(format, filters);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "audit_logs.csv";
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success(
        "`監査ログを${format.toUpperCase()}形式でエクスポートしました`"
      );
    } catch (error) {
      console.error("Failed to export audit logs:", error);
      toast.error("監査ログのエクスポートに失敗しました。");
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-[#2C3E50]">監査ログ</h1>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchLogs}
            disabled={loading}
          >
            <RefreshCw
              className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`}
            />
            更新
          </Button>
          <div className="relative group">
            <Button
              variant="outline"
              size="sm"
              disabled={exporting || logs.length === 0}
            >
              <Download className="w-4 h-4 mr-2" />
              エクスポート
            </Button>
            <div className="absolute right-0 mt-1 w-32 bg-white border rounded-md shadow-lg opacity-0 group-hover:opacity-100 transition-opacity z-10">
              <button
                className="block w-full px-4 py-2 text-sm text-left hover:bg-gray-100"
                onClick={() => handleExport("csv")}
                disabled={exporting}
              >
                CSV形式
              </button>
              <button
                className="block w-full px-4 py-2 text-sm text-left hover:bg-gray-100"
                onClick={() => handleExport("json")}
                disabled={exporting}
              >
                JSON形式
              </button>
            </div>
          </div>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>ログ検索</CardTitle>
        </CardHeader>
        <CardContent>
          <AuditLogFilters
            filters={filters}
            actionTypes={actionTypes}
            resourceTypes={resourceTypes}
            onFiltersChange={handleFiltersChange}
            onReset={handleReset}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle>ログ一覧</CardTitle>
            <span className="text-sm text-gray-500">
              {totalLogs} 件中 {page * itemsPerPage + 1} -{" "}
              {Math.min((page + 1) * itemsPerPage, totalLogs)} 件を表示
            </span>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
            </div>
          ) : (
            <>
              <AuditLogTable logs={logs} />
              {totalLogs > itemsPerPage && (
                <div className="mt-4">
                  <UserPagination
                    page={page}
                    setPage={setPage}
                    totalItems={totalLogs}
                    itemsPerPage={itemsPerPage}
                  />
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
