"use client";

import React, { useEffect, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  deployToDeviceSchema,
  DeployToDeviceFormValues,
} from "@/schemas/deviceSolutionSchemas";
import { toast } from "sonner";
import { Solution } from "@/types/solution";
import { DeviceDeployment } from "@/types/deviceSolution";
import { deviceSolutionService } from "@/services/deviceSolutionService";

interface Customer {
  customer_id: string;
  name: string;
}

interface Device {
  device_id: string;
  name: string;
  device_type: string;
}

interface DeployToDeviceModalProps {
  solution: Solution;
  onClose: () => void;
  onComplete: (deployment: DeviceDeployment) => void;
}

export default function DeployToDeviceModal({
  solution,
  onClose,
  onComplete,
}: DeployToDeviceModalProps) {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [devices, setDevices] = useState<Device[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingDevices, setIsLoadingDevices] = useState(false);

  // React Hook Form setup
  const {
    register,
    handleSubmit,
    control,
    watch,
    setValue,
    formState: { errors },
  } = useForm<DeployToDeviceFormValues>({
    resolver: zodResolver(deployToDeviceSchema),
    defaultValues: {
      version_deployed: solution.version,
    },
  });

  // Watch the customer_id field to update devices when it changes
  const selectedCustomerId = watch("customer_id");

  // Fetch available customers for this solution
  useEffect(() => {
    async function fetchCustomers() {
      try {
        // Get customers that have this solution assigned using the service
        const availableCustomers =
          await deviceSolutionService.getCustomersWithSolutionAccess(
            solution.solution_id
          );
        setCustomers(availableCustomers);
      } catch (error) {
        console.log("Error fetching customers:", error);
        toast.error("顧客の取得に失敗しました", {
          description:
            error instanceof Error
              ? error.message
              : "予期せぬエラーが発生しました",
        });
      }
    }

    fetchCustomers();
  }, [solution.solution_id]);

  // Update available devices when customer changes
  useEffect(() => {
    async function fetchDevices() {
      if (!selectedCustomerId) {
        setDevices([]);
        return;
      }

      setIsLoadingDevices(true);
      try {
        // Get compatible devices for the selected customer
        const compatibleDevices =
          await deviceSolutionService.getCompatibleDevices(
            solution.solution_id,
            selectedCustomerId
          );

        setDevices(compatibleDevices);
      } catch (error) {
        console.log("Error fetching devices:", error);
        toast.error("デバイスの取得に失敗しました", {
          description:
            error instanceof Error
              ? error.message
              : "予期せぬエラーが発生しました",
        });
        setDevices([]);
      } finally {
        setIsLoadingDevices(false);
      }
    }

    fetchDevices();
  }, [selectedCustomerId, solution.solution_id, setValue]);

  const onSubmit = async (data: DeployToDeviceFormValues) => {
    setIsLoading(true);
    try {
      // Create the deployment data
      const deploymentData = {
        device_id: data.device_id,
        solution_id: solution.solution_id,
        version_deployed: data.version_deployed,
        configuration: data.configuration,
      };

      // Call the API to create the deployment
      const deployment =
        await deviceSolutionService.deployToDevice(deploymentData);

      // Call the onComplete callback with the new deployment
      onComplete(deployment);
    } catch (error) {
      console.error("Error creating deployment:", error);
      toast.error("デプロイに失敗しました", {
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
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold text-[#2C3E50]">
            デバイスにソリューションをデプロイ
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 py-4">
          <div className="space-y-2">
            <Label
              htmlFor="customer_id"
              className="text-sm font-medium text-[#7F8C8D]"
            >
              顧客 <span className="text-red-500">*</span>
            </Label>
            <select
              id="customer_id"
              {...register("customer_id")}
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
              <p className="text-xs text-red-500 mt-1">
                {errors.customer_id.message}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label
              htmlFor="device_id"
              className="text-sm font-medium text-[#7F8C8D]"
            >
              デバイス <span className="text-red-500">*</span>
            </Label>
            <select
              id="device_id"
              {...register("device_id")}
              className="w-full h-10 px-3 py-2 text-sm rounded-md border border-[#BDC3C7]"
              disabled={!selectedCustomerId || devices.length === 0}
            >
              <option value="">デバイスを選択</option>
              {devices.map((device) => (
                <option key={device.device_id} value={device.device_id}>
                  {device.name} ({device.device_type})
                </option>
              ))}
            </select>
            {errors.device_id && (
              <p className="text-xs text-red-500 mt-1">
                {errors.device_id.message}
              </p>
            )}
            {selectedCustomerId && devices.length === 0 && (
              <p className="text-xs text-amber-500 mt-1">
                この顧客には、このソリューションと互換性のあるデバイスがありません
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label
              htmlFor="version_deployed"
              className="text-sm font-medium text-[#7F8C8D]"
            >
              デプロイバージョン <span className="text-red-500">*</span>
            </Label>
            <Input
              id="version_deployed"
              {...register("version_deployed")}
              className="w-full h-10 px-3 py-2 text-sm rounded-md border border-[#BDC3C7]"
            />
            {errors.version_deployed && (
              <p className="text-xs text-red-500 mt-1">
                {errors.version_deployed.message}
              </p>
            )}
          </div>

          {/* If there's configuration template, show configuration fields */}
          {solution.configuration_template && (
            <div className="space-y-2">
              <Label
                htmlFor="configuration"
                className="text-sm font-medium text-[#7F8C8D]"
              >
                構成設定
              </Label>
              <Controller
                name="configuration"
                control={control}
                defaultValue={solution.configuration_template}
                render={({ field }) => (
                  <div className="border border-[#BDC3C7] rounded-md p-3">
                    <textarea
                      rows={4}
                      className="w-full text-sm font-mono p-2 border rounded"
                      value={JSON.stringify(field.value, null, 2)}
                      onChange={(e) => {
                        try {
                          field.onChange(JSON.parse(e.target.value));
                        } catch (error) {
                          // Allow invalid JSON during editing
                          field.onChange(e.target.value);
                        }
                      }}
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      JSONフォーマットで構成設定を入力してください
                    </p>
                  </div>
                )}
              />
            </div>
          )}

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
              disabled={
                isLoading || !!(selectedCustomerId && devices.length === 0)
              }
              className="bg-[#27AE60] text-white hover:bg-[#219955]"
            >
              {isLoading ? "デプロイ中..." : "デプロイ"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
