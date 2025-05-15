"use client";

import React, { useEffect, useState } from 'react';
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle,
  DialogFooter
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { assignToCustomerSchema, AssignToCustomerFormValues } from '@/schemas/customerSolutionSchemas';
import { toast } from 'sonner';
import { Solution } from '@/types/solution';
import { CustomerAssignment } from '@/types/customerSolution';
import { customerSolutionService } from '@/services/customerSolutionService';

interface Customer {
    customer_id: string;
    name: string;
  }

interface AssignToCustomerModalProps {
    solution: Solution;
    onClose: () => void;
    onComplete: (assignment: CustomerAssignment) => void;
}

export default function AssignToCustomerModal({ 
    solution, 
    onClose, 
    onComplete 
  }: AssignToCustomerModalProps) {
    const [customers, setCustomers] = useState<Customer[]>([]);
    const [isLoading, setIsLoading] = useState(false);


  // React Hook Form setup
  const { 
    register, 
    handleSubmit, 
    formState: { errors } 
  } = useForm<AssignToCustomerFormValues>({
    resolver: zodResolver(assignToCustomerSchema),
    defaultValues: {
      max_devices: 5,
      license_status: 'ACTIVE',
    }
  });
  // Fetch available customers (those that don't already have this solution)
  useEffect(() => {
    async function fetchCustomers() {
      try {
        // Get available customers directly from the service
        const availableCustomers = await customerSolutionService.getAvailableCustomers(solution.solution_id);
        setCustomers(availableCustomers);
      } catch (error) {
        console.log('Error fetching customers:', error);
        toast.error('顧客の取得に失敗しました', {
          description: error instanceof Error ? error.message : '予期せぬエラーが発生しました',
        });
      }
    }
    
    fetchCustomers();
  }, [solution.solution_id]);

  const onSubmit = async (data: AssignToCustomerFormValues) => {
    setIsLoading(true);
    try {
      // Create the assignment data
      const assignmentData = {
        customer_id: data.customer_id,
        solution_id: solution.solution_id,
        license_status: data.license_status,
        max_devices: data.max_devices,
        expiration_date: data.expiration_date || undefined,
      };
      
      // Call the API to create the assignment
      const assignment = await customerSolutionService.assignToCustomer(assignmentData);
      
      // Call the onComplete callback with the new assignment
      onComplete(assignment);
    } catch (error) {
      console.log('Error creating assignment:', error);
      toast.error('アサインの作成に失敗しました', {
        description: error instanceof Error ? error.message : '予期せぬエラーが発生しました',
      });
    } finally {
      setIsLoading(false);
    }
  };
  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold text-[#2C3E50]">
            顧客にソリューションをアサイン
          </DialogTitle>
        </DialogHeader>
        
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="customer_id" className="text-sm font-medium text-[#7F8C8D]">
              顧客 <span className="text-red-500">*</span>
            </Label>
            <select
              id="customer_id"
              {...register('customer_id')}
              className="w-full h-10 px-3 py-2 text-sm rounded-md border border-[#BDC3C7]"
            >
              <option value="">顧客を選択</option>
              {customers.map((customer) => (
                <option key={customer.customer_id} value={customer.customer_id}>
                  {customer.name}
                </option>
              ))}
            </select>
            {errors.customer_id && (
              <p className="text-xs text-red-500 mt-1">{errors.customer_id.message}</p>
            )}
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="max_devices" className="text-sm font-medium text-[#7F8C8D]">
              最大デバイス数 <span className="text-red-500">*</span>
            </Label>
            <Input
              id="max_devices"
              type="number"
              min="1"
              {...register('max_devices', { valueAsNumber: true })}
              className="w-full h-10 px-3 py-2 text-sm rounded-md border border-[#BDC3C7]"
            />
            {errors.max_devices && (
              <p className="text-xs text-red-500 mt-1">{errors.max_devices.message}</p>
            )}
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="expiration_date" className="text-sm font-medium text-[#7F8C8D]">
              有効期限 (任意)
            </Label>
            <Input
              id="expiration_date"
              type="date"
              {...register('expiration_date')}
              className="w-full h-10 px-3 py-2 text-sm rounded-md border border-[#BDC3C7]"
            />
            <p className="text-xs text-gray-500">空欄の場合は無期限になります</p>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="license_status" className="text-sm font-medium text-[#7F8C8D]">
              ライセンスステータス
            </Label>
            <select
              id="license_status"
              {...register('license_status')}
              className="w-full h-10 px-3 py-2 text-sm rounded-md border border-[#BDC3C7]"
            >
              <option value="ACTIVE">有効</option>
              <option value="SUSPENDED">停止</option>
            </select>
          </div>
          
          <DialogFooter className="pt-4">
            <Button 
              type="button" 
              variant="outline" 
              onClick={onClose}
              disabled={isLoading}
              className="border border-[#BDC3C7] text-[#7F8C8D]"
            >
              キャンセル
            </Button>
            <Button 
              type="submit"
              disabled={isLoading}
              className="bg-[#27AE60] text-white hover:bg-[#219955]"
            >
              {isLoading ? 'アサイン中...' : 'アサイン'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}