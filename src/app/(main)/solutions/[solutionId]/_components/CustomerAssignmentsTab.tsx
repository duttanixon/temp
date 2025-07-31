"use client";

import { Button } from "@/components/ui/button";
import { customerSolutionService } from "@/services/customerSolutionService";
import { CustomerAssignment } from "@/types/customerSolution";
import { Solution } from "@/types/solution";
import { formatDistanceToNow } from "date-fns";
import { ja } from "date-fns/locale";
import { ChevronDown, ChevronUp } from "lucide-react";
import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import AssignToCustomerModal from "./AssignToCustomerModal";

type SortKey =
  | "name"
  | "status"
  | "devices_count"
  | "expiration_date"
  | "assigned_at";
type SortDirection = "asc" | "desc";

interface CustomerAssignmentsTabProps {
  solution: Solution;
  isShowInactive?: boolean;
}

export default function CustomerAssignmentsTab({
  solution,
}: CustomerAssignmentsTabProps) {
  const { data: session } = useSession();
  const [isAssignModalOpen, setIsAssignModalOpen] = useState(false);
  const [assignments, setAssignments] = useState<CustomerAssignment[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isFetching, setIsFetching] = useState(true);

  const isAdmin = session?.user?.role === "ADMIN";
  const [sortKey, setSortKey] = useState<SortKey>("name");
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

  // Fetch customer assignments when component mounts
  useEffect(() => {
    async function fetchAssignments() {
      try {
        setIsFetching(true);
        const data = await customerSolutionService.getCustomerAssignments({
          solutionId: solution.solution_id,
        });
        setAssignments(data);
      } catch (error) {
        console.error("Error fetching assignments:", error);
        toast.error("顧客アサインの取得に失敗しました", {
          description:
            error instanceof Error
              ? error.message
              : "予期せぬエラーが発生しました",
        });
      } finally {
        setIsFetching(false);
      }
    }

    fetchAssignments();
  }, [solution.solution_id]);

  // Handler for assignment completion
  const handleAssignmentComplete = (newAssignment: CustomerAssignment) => {
    toast.success(
      `${newAssignment.customer_name}にソリューションをアサインしました`
    );
    setIsAssignModalOpen(false);
    // Refresh assignments list
    setAssignments((prev) => [...prev, newAssignment]);
  };

  // Handler for status change
  const handleStatusChange = async (
    assignmentId: string,
    customerId: string,
    newStatus: "ACTIVE" | "SUSPENDED"
  ) => {
    setIsLoading(true);
    try {
      let updatedAssignment: any;
      if (newStatus === "ACTIVE") {
        updatedAssignment =
          await customerSolutionService.activateCustomerAssignment(
            customerId,
            solution.solution_id
          );
      } else {
        updatedAssignment =
          await customerSolutionService.suspendCustomerAssignment(
            customerId,
            solution.solution_id
          );
      }

      // Update the assignments list
      setAssignments((prev) =>
        prev.map((a) => (a.id === assignmentId ? updatedAssignment : a))
      );

      toast.success(
        `ライセンスステータスを${newStatus === "ACTIVE" ? "有効" : "停止"}に変更しました`
      );
    } catch (error) {
      console.error("Error updating status:", error);
      toast.error("ステータス変更に失敗しました", {
        description:
          error instanceof Error
            ? error.message
            : "予期せぬエラーが発生しました",
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Handler for assignment removal
  const handleRemoveAssignment = async (
    assignmentId: string,
    customerId: string,
    customerName: string
  ) => {
    if (
      !confirm(
        `${customerName}からこのソリューションを削除してもよろしいですか？`
      )
    ) {
      return;
    }

    setIsLoading(true);
    try {
      await customerSolutionService.removeCustomerAssignment(
        customerId,
        solution.solution_id
      );

      // Remove the assignment from the list
      setAssignments((prev) => prev.filter((a) => a.id !== assignmentId));

      toast.success(`${customerName}からソリューションを削除しました`);
    } catch (error) {
      console.log("Error removing assignment:", error);
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

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-semibold text-[#2C3E50]">顧客アサイン</h2>
        {isAdmin && (
          <Button
            onClick={() => setIsAssignModalOpen(true)}
            className="bg-[#27AE60] text-white hover:bg-[#219955]"
          >
            新規アサイン
          </Button>
        )}
      </div>

      {/* Customer Assignments Table */}
      <div className="overflow-x-auto rounded-lg border border-[#BDC3C7]">
        <table className="min-w-full divide-y divide-[#BDC3C7]">
          <thead className="bg-[#ECF0F1]">
            <tr>
              <th
                className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50] cursor-pointer"
                onClick={() => handleSort("name")}
              >
                <div className="flex justify-center items-center gap-1 select-none">
                  <div className="flex flex-col items-center">
                    <div>顧客名</div>
                    <div className="text-xs text-[#7F8C8D]">Customer</div>
                  </div>
                  {renderSortIcon("name")}
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
              <th
                className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50] cursor-pointer"
                onClick={() => handleSort("devices_count")}
              >
                <div className="flex justify-center items-center gap-1 select-none">
                  <div className="flex flex-col items-center">
                    <div>デバイス数</div>
                    <div className="text-xs text-[#7F8C8D]">Devices</div>
                  </div>
                  {renderSortIcon("devices_count")}
                </div>
              </th>
              <th
                className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50] cursor-pointer"
                onClick={() => handleSort("expiration_date")}
              >
                <div className="flex justify-center items-center gap-1 select-none">
                  <div className="flex flex-col items-center">
                    <div>有効期限</div>
                    <div className="text-xs text-[#7F8C8D]">Expiration</div>
                  </div>
                  {renderSortIcon("expiration_date")}
                </div>
              </th>
              <th
                className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50] cursor-pointer"
                onClick={() => handleSort("assigned_at")}
              >
                <div className="flex justify-center items-center gap-1 select-none">
                  <div className="flex flex-col items-center">
                    <div>アサイン日</div>
                    <div className="text-xs text-[#7F8C8D]">Assigned</div>
                  </div>
                  {renderSortIcon("assigned_at")}
                </div>
              </th>
              {isAdmin && (
                <th className="relative px-6 py-3 text-center text-sm font-semibold text-[#2C3E50]">
                  <div className="absolute left-0 top-0 h-1/2 translate-y-1/2 border-l border-[#BDC3C7]" />
                  <div className="flex justify-center items-center gap-1 select-none">
                    <div className="flex flex-col items-center">
                      <div>アクション</div>
                      <div className="text-xs text-[#7F8C8D]">Actions</div>
                    </div>
                  </div>
                </th>
              )}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-[#BDC3C7]">
            {isFetching ? (
              <tr>
                <td
                  colSpan={isAdmin ? 6 : 5}
                  className="px-6 py-4 text-center text-sm text-[#7F8C8D]"
                >
                  読み込み中...
                </td>
              </tr>
            ) : assignments.length > 0 ? (
              assignments.map((assignment) => (
                <tr key={assignment.id} className="hover:bg-[#F8F9FA]">
                  <td className="px-6 py-4 text-sm text-[#2C3E50] text-center">
                    {assignment.customer_name}
                  </td>
                  <td className="px-6 py-4 text-sm text-center">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        assignment.license_status === "ACTIVE"
                          ? "bg-green-100 text-green-800"
                          : "bg-orange-100 text-orange-800"
                      }`}
                    >
                      {assignment.license_status === "ACTIVE" ? "有効" : "停止"}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-[#2C3E50] text-center">
                    {assignment.devices_count} / {assignment.max_devices}
                  </td>
                  <td className="px-6 py-4 text-sm text-[#2C3E50] text-center">
                    {assignment.expiration_date
                      ? new Date(assignment.expiration_date).toLocaleDateString(
                          "ja-JP"
                        )
                      : "無期限"}
                  </td>
                  <td className="px-6 py-4 text-sm text-[#2C3E50] text-center">
                    {formatDistanceToNow(new Date(assignment.created_at), {
                      addSuffix: true,
                      locale: ja,
                    })}
                  </td>
                  {isAdmin && (
                    <td className="relative px-6 py-4 text-sm space-x-2 text-center">
                      <div className="absolute left-0 top-0 h-1/2 translate-y-1/2 border-l border-[#BDC3C7]" />
                      <button
                        className="text-blue-600 hover:text-blue-800"
                        onClick={() => {
                          /* Would open edit modal */
                        }}
                        disabled={isLoading}
                      >
                        編集
                      </button>
                      <button
                        className={`${
                          assignment.license_status === "ACTIVE"
                            ? "text-orange-600 hover:text-orange-800"
                            : "text-green-600 hover:text-green-800"
                        }`}
                        onClick={() =>
                          handleStatusChange(
                            assignment.id,
                            assignment.customer_id,
                            assignment.license_status === "ACTIVE"
                              ? "SUSPENDED"
                              : "ACTIVE"
                          )
                        }
                        disabled={isLoading}
                      >
                        {assignment.license_status === "ACTIVE"
                          ? "停止"
                          : "有効化"}
                      </button>
                      <button
                        className="text-red-600 hover:text-red-800"
                        onClick={() =>
                          handleRemoveAssignment(
                            assignment.id,
                            assignment.customer_id,
                            assignment.customer_name
                          )
                        }
                        disabled={isLoading}
                      >
                        削除
                      </button>
                    </td>
                  )}
                </tr>
              ))
            ) : (
              <tr>
                <td
                  colSpan={isAdmin ? 6 : 5}
                  className="px-6 py-4 text-center text-sm text-[#7F8C8D]"
                >
                  まだこのソリューションをアサインされた顧客はありません
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Assign to Customer Modal */}
      {isAssignModalOpen && (
        <AssignToCustomerModal
          solution={solution}
          onClose={() => setIsAssignModalOpen(false)}
          onComplete={handleAssignmentComplete}
        />
      )}
    </div>
  );
}
