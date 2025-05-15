"use client";

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { useSession } from 'next-auth/react';
import { toast } from 'sonner';
import { Solution } from '@/types/solution';
import { DeviceDeployment } from '@/types/deviceSolution';
import { deviceSolutionService } from '@/services/deviceSolutionService';
import DeployToDeviceModal from './DeployToDeviceModal';
import { formatDistanceToNow } from 'date-fns';
import { ja } from 'date-fns/locale';


interface DeviceDeploymentsTabProps {
    solution: Solution;
  }


export default function DeviceDeploymentsTab({ solution }: DeviceDeploymentsTabProps) {
    const { data: session } = useSession();
    const [isDeployModalOpen, setIsDeployModalOpen] = useState(false);
    const [deployments, setDeployments] = useState<DeviceDeployment[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [isFetching, setIsFetching] = useState(true);
    const [selectedCustomerId, setSelectedCustomerId] = useState<string>('all');
    const [customers, setCustomers] = useState<{customer_id: string, name: string}[]>([]);

  // Check user permissions
  const isAdmin = session?.user?.role === 'ADMIN';
  const isEngineer = session?.user?.role === 'ENGINEER';
  const isCustomerAdmin = session?.user?.role === 'CUSTOMER_ADMIN';

  // Fetch device deployments when component mounts
  useEffect(() => {
    async function fetchDeployments() {
      try {
        setIsFetching(true);
        const data = await deviceSolutionService.getDeviceDeployments(solution.solution_id);
        setDeployments(data);

        // Extract unique customers from deployments
        const uniqueCustomers = Array.from(
            new Set(data.map(d => d.customer_id))
          ).map(customerId => {
            const deployment = data.find(d => d.customer_id === customerId);
            return {
              customer_id: customerId,
              name: deployment?.customer_name || 'Unknown'
            };
          });
          setCustomers(uniqueCustomers);
        } catch (error) {
            console.log('Error fetching deployments:', error);
            toast.error('デプロイの取得に失敗しました', {
              description: error instanceof Error ? error.message : '予期せぬエラーが発生しました',
            });
          } finally {
            setIsFetching(false);
          }
        }
        
        fetchDeployments();
      }, [solution.solution_id]);

  // Filter deployments by selected customer
  const filteredDeployments = selectedCustomerId === 'all'
    ? deployments
    : deployments.filter(d => d.customer_id === selectedCustomerId);

  // Handler for deployment completion
  const handleDeploymentComplete = (newDeployment: DeviceDeployment) => {
    toast.success(`ソリューションを${newDeployment.device_name}にデプロイしました`);
    setIsDeployModalOpen(false);
    // Add the new deployment to the list
    setDeployments(prev => [...prev, newDeployment]);
    
    // Add the customer to the customers list if it's not already there
    if (!customers.some(c => c.customer_id === newDeployment.customer_id)) {
      setCustomers(prev => [...prev, {
        customer_id: newDeployment.customer_id,
        name: newDeployment.customer_name
      }]);
    }
  };

  // Handler for removing a deployment
  const handleRemoveDeployment = async (deviceId: string, deviceName: string) => {
    if (!confirm(`${deviceName}からこのソリューションを削除してもよろしいですか？`)) {
      return;
    }
    
    setIsLoading(true);
    try {
      await deviceSolutionService.removeDeviceDeployment(deviceId);
      
      // Remove the deployment from the list
      setDeployments(prev => prev.filter(d => d.device_id !== deviceId));
      
      toast.success(`${deviceName}からソリューションを削除しました`);
    } catch (error) {
      console.log('Error removing deployment:', error);
      toast.error('削除に失敗しました', {
        description: error instanceof Error ? error.message : '予期せぬエラーが発生しました',
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Helper function to get status badge style
  const getStatusBadgeStyle = (status: string) => {
    switch (status) {
      case 'ACTIVE':
        return 'bg-green-100 text-green-800';
      case 'PROVISIONING':
        return 'bg-blue-100 text-blue-800';
      case 'ERROR':
        return 'bg-red-100 text-red-800';
      case 'STOPPED':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // Helper function to get status label
  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'ACTIVE':
        return '稼働中';
      case 'PROVISIONING':
        return 'プロビジョニング中';
      case 'ERROR':
        return 'エラー';
      case 'STOPPED':
        return '停止';
      default:
        return status;
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-semibold text-[#2C3E50]">デバイスデプロイ</h2>
          <Button 
            onClick={() => setIsDeployModalOpen(true)}
            className="bg-[#27AE60] text-white hover:bg-[#219955]"
          >
            新規デプロイ
          </Button>

      </div>

      {/* Filter by customer */}
      <div className="flex items-center gap-2">
        <label htmlFor="customer-filter" className="text-sm font-medium text-[#7F8C8D]">
          顧客フィルター:
        </label>
        <select
          id="customer-filter"
          value={selectedCustomerId}
          onChange={(e) => setSelectedCustomerId(e.target.value)}
          className="px-3 py-1 text-sm rounded-md border border-[#BDC3C7]"
        >
          <option value="all">すべての顧客</option>
          {customers.map((customer) => (
            <option key={customer.customer_id} value={customer.customer_id}>
              {customer.name}
            </option>
          ))}
        </select>
      </div>

      {/* Device Deployments Table */}
      <div className="overflow-x-auto rounded-lg border border-[#BDC3C7]">
        <table className="min-w-full divide-y divide-[#BDC3C7]">
          <thead className="bg-[#ECF0F1]">
            <tr>
                <th className="px-6 py-3 text-left text-sm font-semibold text-[#2C3E50]">デバイス名</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-[#2C3E50]">顧客名</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-[#2C3E50]">ステータス</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-[#2C3E50]">バージョン</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-[#2C3E50]">最終更新</th>
                <th className="px-6 py-3 text-right text-sm font-semibold text-[#2C3E50]">アクション</th>

            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-[#BDC3C7]">
            {isFetching ? (
              <tr>
                <td 
                  colSpan={ 6} 
                  className="px-6 py-4 text-center text-sm text-[#7F8C8D]"
                >
                  読み込み中...
                </td>
              </tr>
            ) : filteredDeployments.length > 0 ? (
              filteredDeployments.map((deployment) => (
                <tr key={deployment.id} className="hover:bg-[#F8F9FA]">
                  <td className="px-6 py-4 text-sm text-[#2C3E50]">{deployment.device_name}</td>
                  <td className="px-6 py-4 text-sm text-[#2C3E50]">{deployment.customer_name}</td>
                  <td className="px-6 py-4 text-sm">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      getStatusBadgeStyle(deployment.status)
                    }`}>
                      {getStatusLabel(deployment.status)}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-[#2C3E50]">{deployment.version_deployed}</td>
                  <td className="px-6 py-4 text-sm text-[#2C3E50]">
                    {deployment.last_update 
                      ? formatDistanceToNow(new Date(deployment.last_update), {
                          addSuffix: true,
                          locale: ja,
                        })
                      : formatDistanceToNow(new Date(deployment.created_at), {
                          addSuffix: true,
                          locale: ja,
                        }) + ' (初回デプロイ)'}
                  </td>
                    <td className="px-6 py-4 text-sm text-right space-x-2">
                      <button 
                        className="text-blue-600 hover:text-blue-800"
                        onClick={() => {/* Would open update modal */}}
                        disabled={isLoading}
                      >
                        更新
                      </button>
                      <button 
                        className="text-red-600 hover:text-red-800"
                        onClick={() => handleRemoveDeployment(deployment.device_id, deployment.device_name)}
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
                  {selectedCustomerId === 'all'
                    ? 'まだこのソリューションがデプロイされたデバイスはありません'
                    : 'この顧客には、このソリューションがデプロイされたデバイスはありません'}
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