import { useGetCustomer } from "@/app/(main)/_components/_hooks/useGetCustomer";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Checkbox } from "@components/ui/checkbox";
import { AlertCircle, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import { FilterCard } from "./FilterCard";

interface CustomerInfo {
  customer_id: string;
  name: string;
}

interface CustomersFilterProps {
  selectedCustomers: string[];
  onSelectionChange: (selectedCustomers: string[]) => void;
  icon?: React.ReactNode;
  iconBgColor?: string;
  collapsible?: boolean;
  defaultExpanded?: boolean;
}

export function CustomerFilter({
  selectedCustomers,
  onSelectionChange,
  icon,
  iconBgColor,
  collapsible = true,
  defaultExpanded = false,
}: CustomersFilterProps) {
  const { customer, isLoading, error } = useGetCustomer();
  const [availableCustomers, setAvailableCustomers] = useState<CustomerInfo[]>(
    []
  );

  const isAllSelected =
    availableCustomers.length > 0 &&
    selectedCustomers.length === availableCustomers.length;

  const selectionSummary = `(${selectedCustomers.length}/${availableCustomers.length})`;

  useEffect(() => {
    if (customer) {
      setAvailableCustomers(customer);
    }
  }, [customer]);

  const handleCustomerToggle = (customerId: string) => {
    const newSelectedCustomers = selectedCustomers.includes(customerId)
      ? selectedCustomers.filter((id) => id !== customerId)
      : [...selectedCustomers, customerId];
    onSelectionChange(newSelectedCustomers);
  };

  const handleSelectAllToggle = () => {
    if (isAllSelected) {
      onSelectionChange([]);
    } else {
      onSelectionChange(availableCustomers.map((c) => c.customer_id));
    }
  };

  const renderContent = () => {
    if (isLoading) {
      return (
        <div className="flex items-center justify-center py-8">
          <div className="flex flex-col items-center gap-2">
            <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
            <span className="text-sm text-slate-500">顧客を読み込み中...</span>
          </div>
        </div>
      );
    }

    if (error) {
      return (
        <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
          <AlertCircle className="h-4 w-4 text-red-500 flex-shrink-0" />
          <span className="text-sm text-red-700">{error}</span>
        </div>
      );
    }

    if (availableCustomers.length === 0) {
      return (
        <div className="flex items-center gap-2 p-3 bg-amber-50 border border-amber-200 rounded-lg">
          <AlertCircle className="h-4 w-4 text-amber-500 flex-shrink-0" />
          <span className="text-sm text-amber-700">
            このソリューションに紐づく利用可能な顧客がありません。
          </span>
        </div>
      );
    }

    return (
      <div className="space-y-3">
        <div className="flex items-center space-x-2 p-1 hover:bg-state-50 rounded-lg transition-colors duration-200 group">
          <Checkbox
            id="select-all-customers"
            checked={isAllSelected}
            onCheckedChange={handleSelectAllToggle}
            className="data-[state=checked]:bg-blue-500 data-[state=checked]:border-blue-500 cursor-pointer"
          />
          <Label
            htmlFor="select-all-customers"
            className="text-sm font-medium text-slate-700 group-hover:text-slate-900 cursor-pointer"
          >
            すべて
          </Label>
        </div>
        <div>
          <div className="text-xs text-slate-500 medium mb-2">個別選択:</div>
          <ScrollArea className="max-h-40">
            <div className="space-y-1 pr-3">
              {availableCustomers.map((customer) => {
                const displayName = `${customer.name || "N/A"}`;
                return (
                  <div
                    key={customer.customer_id}
                    className="flex items-center space-x-2 p-1 hover:bg-state-50 rounded-lg transition-colors duration-200 group"
                  >
                    <Checkbox
                      id={`customer-${customer.customer_id}`}
                      checked={selectedCustomers.includes(customer.customer_id)}
                      onCheckedChange={() =>
                        handleCustomerToggle(customer.customer_id)
                      }
                      className="data-[state=checked]:bg-blue-500 data-[state=checked]:border-blue-500 cursor-pointer"
                    />
                    <Label
                      htmlFor={`customer-${customer.customer_id}`}
                      className="text-sm font-medium text-slate-700 group-hover:text-slate-900 cursor-pointer"
                    >
                      {displayName}
                    </Label>
                  </div>
                );
              })}
            </div>
          </ScrollArea>
        </div>
      </div>
    );
  };
  return (
    <FilterCard
      title="顧客"
      icon={icon}
      iconBgColor={iconBgColor}
      collapsible={collapsible}
      defaultExpanded={defaultExpanded}
      selectionSummary={selectionSummary}
    >
      {renderContent()}
    </FilterCard>
  );
}
