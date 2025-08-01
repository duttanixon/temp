"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { deviceSolutionService } from "@/services/deviceSolutionService";
import { DeviceDeployment } from "@/types/deviceSolution";
import { Solution } from "@/types/solution";
import { formatDistanceToNow } from "date-fns";
import { ja } from "date-fns/locale";
import { ChevronDown, ChevronUp, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import DeployToDeviceModal from "./DeployToDeviceModal";

type SortKey = "device_name" | "customer_name" | "status";
type SortDirection = "asc" | "desc";

interface DeviceDeploymentsTabProps {
  solution: Solution;
}

export default function DeviceDeploymentsTab({
  solution,
}: DeviceDeploymentsTabProps) {
  const [isDeployModalOpen, setIsDeployModalOpen] = useState(false);
  const [deployments, setDeployments] = useState<DeviceDeployment[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isFetching, setIsFetching] = useState(true);
  const [selectedCustomerId, setSelectedCustomerId] = useState<string>("all");
  const [customers, setCustomers] = useState<
    { customer_id: string; name: string }[]
  >([]);

  const [sortKey, setSortKey] = useState<SortKey>("device_name");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");
  const handleSort = (key: SortKey) => {
    if (key === sortKey) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDirection("asc");
    }
  };

  const renderSortIcon = (key: SortKey) => {
    return sortKey === key ? (
      sortDirection === "asc" ? (
        <ChevronUp size={16} />
      ) : (
        <ChevronDown size={16} />
      )
    ) : null;
  };

  // Fetch device deployments when component mounts
  useEffect(() => {
    async function fetchDeployments() {
      try {
        setIsFetching(true);
        const data = await deviceSolutionService.getDeviceDeployments(
          solution.solution_id
        );
        setDeployments(data);

        // Extract unique customers from deployments
        const uniqueCustomers = Array.from(
          new Set(data.map((d) => d.customer_id))
        ).map((customerId) => {
          const deployment = data.find((d) => d.customer_id === customerId);
          return {
            customer_id: customerId,
            name: deployment?.customer_name || "Unknown",
          };
        });
        setCustomers(uniqueCustomers);
      } catch (error) {
        console.log("Error fetching deployments:", error);
        toast.error("デプロイの取得に失敗しました", {
          description:
            error instanceof Error
              ? error.message
              : "予期せぬエラーが発生しました",
        });
      } finally {
        setIsFetching(false);
      }
    }

    fetchDeployments();
  }, [solution.solution_id]);

  const [query, setQuery] = useState("");

  // Filter deployments by selected customer
  const filteredDeployments = useMemo(() => {
    return deployments
      .filter((deployment) => {
        if (selectedCustomerId === "all") return true;
        return deployment.customer_id === selectedCustomerId;
      })
      .filter((deployment) =>
        deployment.device_name.toLowerCase().includes(query.toLowerCase())
      )
      .sort((a, b) => {
        const aValue = a[sortKey];
        const bValue = b[sortKey];
        if (aValue < bValue) return sortDirection === "asc" ? -1 : 1;
        if (aValue > bValue) return sortDirection === "asc" ? 1 : -1;
        return 0;
      });
  }, [deployments, selectedCustomerId, query, sortKey, sortDirection]);
  // Handler for deployment completion
  const handleDeploymentComplete = (newDeployment: DeviceDeployment) => {
    toast.success(
      `ソリューションを${newDeployment.device_name}にデプロイしました`
    );
    setIsDeployModalOpen(false);
    // Add the new deployment to the list
    setDeployments((prev) => [...prev, newDeployment]);

    // Add the customer to the customers list if it's not already there
    if (!customers.some((c) => c.customer_id === newDeployment.customer_id)) {
      setCustomers((prev) => [
        ...prev,
        {
          customer_id: newDeployment.customer_id,
          name: newDeployment.customer_name,
        },
      ]);
    }
  };

  // Handler for removing a deployment
  const handleRemoveDeployment = async (
    deviceId: string,
    deviceName: string
  ) => {
    if (
      !confirm(
        `${deviceName}からこのソリューションを削除してもよろしいですか？`
      )
    ) {
      return;
    }

    setIsLoading(true);
    try {
      await deviceSolutionService.removeDeviceDeployment(deviceId);

      // Remove the deployment from the list
      setDeployments((prev) => prev.filter((d) => d.device_id !== deviceId));

      toast.success(`${deviceName}からソリューションを削除しました`);
    } catch (error) {
      console.log("Error removing deployment:", error);
      toast.error("削除に失敗しました", {
        description:
          error instanceof Error
            ? error.message
            : "予期せぬエラーが発生しました",
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Helper function to get status badge style
  const getStatusBadgeStyle = (status: string) => {
    switch (status) {
      case "ACTIVE":
        return "bg-green-100 text-green-800";
      case "PROVISIONING":
        return "bg-blue-100 text-blue-800";
      case "ERROR":
        return "bg-red-100 text-red-800";
      case "STOPPED":
        return "bg-gray-100 text-gray-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  // Helper function to get status label
  const getStatusLabel = (status: string) => {
    switch (status) {
      case "ACTIVE":
        return "稼働中";
      case "PROVISIONING":
        return "プロビジョニング中";
      case "ERROR":
        return "エラー";
      case "STOPPED":
        return "停止";
      default:
        return status;
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-semibold text-[#2C3E50]">
          デバイスデプロイ
        </h2>
        <Button
          onClick={() => setIsDeployModalOpen(true)}
          className="bg-[#27AE60] text-white hover:bg-[#219955]"
        >
          新規デプロイ
        </Button>
      </div>

      {/* Filter by customer */}
      <div className="inline-block border border-gray-400 rounded-md px-4 py-3 bg-white overflow-hidden">
        <div className="flex items-end gap-6 flex-wrap">
          <div className="flex flex-col flex-1 items-start gap-1">
            <label htmlFor="customer-filter" className="text-sm">
              顧客
            </label>
            <select
              id="customer-filter"
              value={selectedCustomerId}
              onChange={(e) => setSelectedCustomerId(e.target.value)}
              className="px-3 py-1 text-sm rounded-md border border-[#BDC3C7]"
            >
              <option value="all">すべて</option>
              {customers.map((customer) => (
                <option key={customer.customer_id} value={customer.customer_id}>
                  {customer.name}
                </option>
              ))}
            </select>
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

      {/* Device Deployments Table */}
      <div className="overflow-x-auto rounded-lg border border-[#BDC3C7]">
        <table className="min-w-full divide-y divide-[#BDC3C7]">
          <thead className="bg-[#ECF0F1]">
            <tr>
              <th
                className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50] cursor-pointer"
                onClick={() => handleSort("device_name")}
              >
                <div className="flex justify-center items-center gap-1 select-none">
                  <div className="flex flex-col items-center">
                    <div>デバイス名</div>
                    <div className="text-xs text-[#7F8C8D]">Device Name</div>
                  </div>
                  {renderSortIcon("device_name")}
                </div>
              </th>

              <th
                className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50] cursor-pointer"
                onClick={() => handleSort("customer_name")}
              >
                <div className="flex justify-center items-center gap-1 select-none">
                  <div className="flex flex-col items-center">
                    <div>顧客名</div>
                    <div className="text-xs text-[#7F8C8D]">Customer Name</div>
                  </div>
                  {renderSortIcon("customer_name")}
                </div>
              </th>
              <th
                className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50] cursor-pointer"
                onClick={() => handleSort("status")}
              >
                <div className="flex justify-center items-center gap-1 select-none">
                  <div className="flex flex-col items-center">
                    <div>ステータス</div>
                    <div className="text-xs text-[#7F8C8D]">Status</div>
                  </div>
                  {renderSortIcon("status")}
                </div>
              </th>
              <th className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50]">
                <div className="flex justify-center items-center gap-1 select-none">
                  <div className="flex flex-col items-center">
                    <div>バージョン</div>
                    <div className="text-xs text-[#7F8C8D]">Version</div>
                  </div>
                </div>
              </th>
              <th className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50]">
                <div className="flex justify-center items-center gap-1 select-none">
                  <div className="flex flex-col items-center">
                    <div>最終更新</div>
                    <div className="text-xs text-[#7F8C8D]">Last Updated</div>
                  </div>
                </div>
              </th>
              <th className="relative px-6 py-3 text-center text-sm font-semibold text-[#2C3E50]">
                <div className="absolute left-0 top-0 h-1/2 translate-y-1/2 border-l border-[#BDC3C7]" />
                <div className="flex justify-center items-center gap-1 select-none">
                  <div className="flex flex-col items-center">
                    <div>アクション</div>
                    <div className="text-xs text-[#7F8C8D]">Actions</div>
                  </div>
                </div>
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-[#BDC3C7]">
            {isFetching ? (
              <tr>
                <td
                  colSpan={6}
                  className="px-6 py-4 text-center text-sm text-[#7F8C8D]"
                >
                  読み込み中...
                </td>
              </tr>
            ) : filteredDeployments.length > 0 ? (
              filteredDeployments.map((deployment) => (
                <tr key={deployment.id} className="hover:bg-[#F8F9FA]">
                  <td className="px-6 py-4 text-sm text-[#2C3E50]">
                    {deployment.device_name}
                  </td>
                  <td className="px-6 py-4 text-sm text-[#2C3E50]">
                    {deployment.customer_name}
                  </td>
                  <td className="px-6 py-4 text-sm text-center">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadgeStyle(
                        deployment.status
                      )}`}
                    >
                      {getStatusLabel(deployment.status)}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-[#2C3E50] text-center">
                    {deployment.version_deployed}
                  </td>
                  <td className="px-6 py-4 text-sm text-[#2C3E50] text-center">
                    {deployment.last_update
                      ? formatDistanceToNow(new Date(deployment.last_update), {
                          addSuffix: true,
                          locale: ja,
                        })
                      : formatDistanceToNow(new Date(deployment.created_at), {
                          addSuffix: true,
                          locale: ja,
                        }) + " (初回デプロイ)"}
                  </td>
                  <td className="relative px-6 py-4 text-sm space-x-2 text-center">
                    <div className="absolute left-0 top-0 h-1/2 translate-y-1/2 border-l border-[#BDC3C7]" />
                    <button
                      className="text-blue-600 hover:text-blue-800 cursor-pointer"
                      onClick={() => {
                        /* Would open update modal */
                      }}
                      disabled={isLoading}
                    >
                      更新
                    </button>
                    <button
                      className="text-red-600 hover:text-red-800 cursor-pointer"
                      onClick={() =>
                        handleRemoveDeployment(
                          deployment.device_id,
                          deployment.device_name
                        )
                      }
                      disabled={isLoading}
                    >
                      削除
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
                  {selectedCustomerId === "all"
                    ? "まだこのソリューションがデプロイされたデバイスはありません"
                    : "この顧客には、このソリューションがデプロイされたデバイスはありません"}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Deploy to Device Modal */}
      {isDeployModalOpen && (
        <DeployToDeviceModal
          solution={solution}
          onClose={() => setIsDeployModalOpen(false)}
          onComplete={handleDeploymentComplete}
        />
      )}
    </div>
  );
}
