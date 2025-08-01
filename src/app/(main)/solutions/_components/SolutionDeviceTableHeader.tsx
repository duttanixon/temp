/*
 * This component list all table header for the device table, common accross all application
 */

import { ChevronDown, ChevronUp } from "lucide-react";
import { type FC } from "react";

type SortKey = "name" | "device_type" | "customer_name";
type SortDirection = "asc" | "desc";

type DeviceTableHeaderProps = {
  sortKey: SortKey;
  sortDirection: SortDirection;
  onSort: (key: SortKey) => void;
};

/**
 * DeviceTableHeader Component
 */
export const SolutionDeviceTableHeader: FC<DeviceTableHeaderProps> = ({
  sortKey,
  sortDirection,
  onSort,
}) => {
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
      <th
        onClick={() => onSort("name")}
        className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50] cursor-pointer">
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
        className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50] cursor-pointer">
        <div className="flex justify-center items-center gap-1 select-none">
          <div className="flex flex-col items-center">
            <div>タイプ</div>
            <div className="text-xs text-[#7F8C8D]">Type</div>
          </div>
          {renderSortIcon("device_type")}
        </div>
      </th>
      <th
        onClick={() => onSort("customer_name")}
        className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50] cursor-pointer">
        <div className="flex justify-center items-center gap-1 select-none">
          <div className="flex flex-col items-center">
            <div>顧客名</div>
            <div className="text-xs text-[#7F8C8D]">Customer</div>
          </div>
          {renderSortIcon("customer_name")}
        </div>
      </th>
      <th className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50]">
        <div className="flex flex-col items-center">
          <div>最終接続</div>
          <div className="text-xs text-[#7F8C8D]">Last Connected</div>
        </div>
      </th>
      <th className="relative px-6 py-3 text-center text-sm font-semibold text-[#2C3E50]">
        <div className="absolute left-0 top-0 h-1/2 translate-y-1/2 border-l border-[#BDC3C7]" />
        <div className="flex flex-col items-center">
          <div>アクション</div>
          <div className="text-xs text-[#7F8C8D]">Actions</div>
        </div>
      </th>
    </tr>
  );
};
