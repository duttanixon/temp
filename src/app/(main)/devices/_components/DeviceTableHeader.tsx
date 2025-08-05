/*
 * This component list all table header for the device table, common accross all application
 */

import { Checkbox } from "@/components/ui/checkbox";
import { ChevronDown, ChevronUp } from "lucide-react";
import { useSession } from "next-auth/react";
import { type FC } from "react";

type SortKey =
  | "name"
  | "device_type"
  | "customer_name"
  | "solution_name"
  | "last_connected";
type SortDirection = "asc" | "desc";

type DeviceTableHeaderProps = {
  sortKey: SortKey;
  sortDirection: SortDirection;
  onSort: (key: SortKey) => void;
  onCheckedChange: (checked: boolean) => void;
  selectedDevices?: string[];
  devices?: { device_id: string }[];
};

/**
 * DeviceTableHeader Component
 */
export const DeviceTableHeader: FC<DeviceTableHeaderProps> = ({
  sortKey,
  sortDirection,
  onSort,
  onCheckedChange,
  selectedDevices = [],
  devices = [],
}) => {
  const { data: session } = useSession();
  const role = session?.user?.role;
  const renderSortIcon = (key: SortKey) => {
    return sortKey === key ? (
      sortDirection === "asc" ? (
        <ChevronUp size={16} />
      ) : (
        <ChevronDown size={16} />
      )
    ) : null;
  };

  return (
    <tr>
      <th className="px-6 py-3 text-center">
        <Checkbox
          checked={
            selectedDevices.length === devices.length && devices.length > 0
          }
          onCheckedChange={onCheckedChange}
          className="w-5 h-5  border-gray-400"
        />
      </th>
      <th
        onClick={() => onSort("name")}
        className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50] cursor-pointer"
      >
        <div className="flex justify-center items-center gap-1 select-none">
          <div className="flex flex-col items-center">
            <div>デバイス名</div>
            <div className="text-xs text-[#7F8C8D]">Device Name</div>
          </div>
          {renderSortIcon("name")}
        </div>
      </th>
      <th
        onClick={() => onSort("device_type")}
        className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50] cursor-pointer"
      >
        <div className="flex justify-center items-center gap-1 select-none">
          <div className="flex flex-col items-center">
            <div>タイプ</div>
            <div className="text-xs text-[#7F8C8D]">Type</div>
          </div>
          {renderSortIcon("device_type")}
        </div>
      </th>
      {(role === "ADMIN" || role === "ENGINEER") && (
        <th
          onClick={() => onSort("customer_name")}
          className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50] cursor-pointer"
        >
          <div className="flex justify-center items-center gap-1 select-none">
            <div className="flex flex-col items-center">
              <div>顧客名</div>
              <div className="text-xs text-[#7F8C8D]">Customer Name</div>
            </div>
            {renderSortIcon("customer_name")}
          </div>
        </th>
      )}
      <th
        onClick={() => onSort("solution_name")}
        className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50] cursor-pointer"
      >
        <div className="flex justify-center items-center gap-1 select-none">
          <div className="flex flex-col items-center">
            <div>ソリューション</div>
            <div className="text-xs text-[#7F8C8D]">Solution</div>
          </div>
          {renderSortIcon("solution_name")}
        </div>
      </th>
      <th className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50]">
        <div className="flex justify-center items-center gap-1 select-none">
          <div className="flex flex-col items-center">
            <div>ジョブ状況</div>
            <div className="text-xs text-[#7F8C8D]">Job Status</div>
          </div>
        </div>
      </th>
      <th
        onClick={() => onSort("last_connected")}
        className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50] cursor-pointer"
      >
        <div className="flex justify-center items-center gap-1 select-none">
          <div className="flex flex-col items-center">
            <div>最終接続</div>
            <div className="text-xs text-[#7F8C8D]">Last Connected</div>
          </div>
          {renderSortIcon("last_connected")}
        </div>
      </th>
    </tr>
  );
};
