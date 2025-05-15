"use client";

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { useSession } from 'next-auth/react';
import { toast } from 'sonner';
import { Solution } from '@/types/solution';
import { CustomerAssignment } from '@/types/customerSolution';
import { customerSolutionService } from '@/services/customerSolutionService';
import AssignToCustomerModal from './AssignToCustomerModal';
import { formatDistanceToNow } from 'date-fns';
import { ja } from 'date-fns/locale';

interface CustomerAssignmentsTabProps {
    solution: Solution;
  }
  
  export default function CustomerAssignmentsTab({ solution }: CustomerAssignmentsTabProps) {
    const { data: session } = useSession();
    const [isAssignModalOpen, setIsAssignModalOpen] = useState(false);
    const [assignments, setAssignments] = useState<CustomerAssignment[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [isFetching, setIsFetching] = useState(true);

    const isAdmin = session?.user?.role === 'ADMIN';

    // Fetch customer assignments when component mounts
    useEffect(() => {
        async function fetchAssignments() {
          try {
            setIsFetching(true);
            const data = await customerSolutionService.getCustomerAssignments(solution.solution_id);
            setAssignments(data);
          } catch (error) {
            console.error('Error fetching assignments:', error);
            toast.error('顧客アサインの取得に失敗しました', {
              description: error instanceof Error ? error.message : '予期せぬエラーが発生しました',
            });
          } finally {
            setIsFetching(false);
          }
        }
        
        fetchAssignments();
      }, [solution.solution_id]);

    // Handler for assignment completion
    const handleAssignmentComplete = (newAssignment: CustomerAssignment) => {
        toast.success(`${newAssignment.customer_name}にソリューションをアサインしました`);
        setIsAssignModalOpen(false);
        // Refresh assignments list
        setAssignments(prev => [...prev, newAssignment]);
    };

  // Handler for status change
  const handleStatusChange = async (assignmentId: string, customerId: string, newStatus: 'ACTIVE' | 'SUSPENDED') => {
    setIsLoading(true);
    try {
      let updatedAssignment: any;
      if (newStatus === 'ACTIVE') {
        updatedAssignment = await customerSolutionService.activateCustomerAssignment(
          customerId, 
          solution.solution_id
        );
      } else {
        updatedAssignment = await customerSolutionService.suspendCustomerAssignment(
          customerId, 
          solution.solution_id
        );
      }
      
      // Update the assignments list
      setAssignments(prev => 
        prev.map(a => a.id === assignmentId ? updatedAssignment : a)
      );
      
      toast.success(`ライセンスステータスを${newStatus === 'ACTIVE' ? '有効' : '停止'}に変更しました`);
    } catch (error) {
      console.error('Error updating status:', error);
      toast.error('ステータス変更に失敗しました', {
        description: error instanceof Error ? error.message : '予期せぬエラーが発生しました',
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Handler for assignment removal
  const handleRemoveAssignment = async (assignmentId: string, customerId: string, customerName: string) => {
    if (!confirm(`${customerName}からこのソリューションを削除してもよろしいですか？`)) {
      return;
    }
    
    setIsLoading(true);
    try {
      await customerSolutionService.removeCustomerAssignment(
        customerId, 
        solution.solution_id
      );
      
      // Remove the assignment from the list
      setAssignments(prev => prev.filter(a => a.id !== assignmentId));
      
      toast.success(`${customerName}からソリューションを削除しました`);
    } catch (error) {
      console.log('Error removing assignment:', error);
      toast.error('削除に失敗しました', {
        description: error instanceof Error ? error.message : '予期せぬエラーが発生しました',
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
              <th className="px-6 py-3 text-left text-sm font-semibold text-[#2C3E50]">顧客名</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-[#2C3E50]">ステータス</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-[#2C3E50]">デバイス数</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-[#2C3E50]">有効期限</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-[#2C3E50]">アサイン日</th>
              {isAdmin && (
                <th className="px-6 py-3 text-right text-sm font-semibold text-[#2C3E50]">アクション</th>
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
                  <td className="px-6 py-4 text-sm text-[#2C3E50]">{assignment.customer_name}</td>
                  <td className="px-6 py-4 text-sm">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      assignment.license_status === 'ACTIVE' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-orange-100 text-orange-800'
                    }`}>
                      {assignment.license_status === 'ACTIVE' ? '有効' : '停止'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-[#2C3E50]">
                    {assignment.devices_count} / {assignment.max_devices}
                  </td>
                  <td className="px-6 py-4 text-sm text-[#2C3E50]">
                    {assignment.expiration_date 
                      ? new Date(assignment.expiration_date).toLocaleDateString('ja-JP')
                      : '無期限'}
                  </td>
                  <td className="px-6 py-4 text-sm text-[#2C3E50]">
                    {formatDistanceToNow(new Date(assignment.created_at), {
                      addSuffix: true,
                      locale: ja,
                    })}
                  </td>
                  {isAdmin && (
                    <td className="px-6 py-4 text-sm text-right space-x-2">
                      <button 
                        className="text-blue-600 hover:text-blue-800"
                        onClick={() => {/* Would open edit modal */}}
                        disabled={isLoading}
                      >
                        編集
                      </button>
                      <button 
                        className={`${
                          assignment.license_status === 'ACTIVE' 
                            ? 'text-orange-600 hover:text-orange-800' 
                            : 'text-green-600 hover:text-green-800'
                        }`}
                        onClick={() => handleStatusChange(
                          assignment.id, 
                          assignment.customer_id,
                          assignment.license_status === 'ACTIVE' ? 'SUSPENDED' : 'ACTIVE'
                        )}
                        disabled={isLoading}
                      >
                        {assignment.license_status === 'ACTIVE' ? '停止' : '有効化'}
                      </button>
                      <button 
                        className="text-red-600 hover:text-red-800"
                        onClick={() => handleRemoveAssignment(
                          assignment.id, 
                          assignment.customer_id,
                          assignment.customer_name
                        )}
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