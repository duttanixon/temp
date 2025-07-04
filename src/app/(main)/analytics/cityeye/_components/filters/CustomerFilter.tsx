import { useGetCustomer } from "@/app/(main)/_components/_hooks/useGetCustomer";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
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

  const selectionSummary = `(${selectedCustomers.length}/${availableCustomers.length})`;

  useEffect(() => {
    if (customer) {
      setAvailableCustomers(customer);
    }
  }, [customer]);

  useEffect(() => {
    if (
      availableCustomers.length > 0 &&
      (selectedCustomers.length === 0 ||
        !availableCustomers.some((c) => c.customer_id === selectedCustomers[0]))
    ) {
      onSelectionChange([availableCustomers[0].customer_id]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [availableCustomers, selectedCustomers]);

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
        <Label className="text-xs text-slate-500 font-medium">顧客選択</Label>
        <Select
          value={selectedCustomers[0] || ""}
          onValueChange={(value) => {
            if (value) {
              onSelectionChange([value]);
            } else {
              onSelectionChange([]);
            }
          }}
        >
          <SelectTrigger className="w-full">
            <SelectValue placeholder="顧客を選択してください" />
          </SelectTrigger>
          <SelectContent>
            {availableCustomers.map((customer) => (
              <SelectItem
                key={customer.customer_id}
                value={customer.customer_id}
              >
                {customer.name || "N/A"}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
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
