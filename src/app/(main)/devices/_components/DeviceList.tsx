/*
 * This component host all the devicetable based on application, common accross all application
 */

"use client";

import { Device } from "@/types/device";
import { useMemo, useState } from "react";
import DevicePagination from "../../users/_components/Pagination";
import DeviceFilters from "./DeviceFilters";
import { DeviceTable } from "./DeviceTable";

interface DeviceListProps {
  initialDevices: Device[];
}

export default function DeviceList({ initialDevices }: DeviceListProps) {
  const [deviceType, setDeviceType] = useState("");
  const [customerId, setCustomerId] = useState("");
  const [solutionName, setSolutionName] = useState("");
  const [page, setPage] = useState(0);
  const [query, setQuery] = useState("");
  const itemsPerPage = 10;

  const filteredDevices = useMemo(() => {
    const q = query.toLowerCase();
    return initialDevices.filter((device) => {
      const matchesDeviceType =
        !deviceType || device.device_type === deviceType;
      const matchesCustomer = !customerId || device.customer_id === customerId;
      const matchesSolution =
        !solutionName || device.solution_name === solutionName;
      const matchesQuery = !q || device.name.toLowerCase().includes(q);
      return (
        matchesDeviceType && matchesCustomer && matchesSolution && matchesQuery
      );
    });
  }, [initialDevices, deviceType, customerId, solutionName, query]);
  console.log("Filtered Devices:", initialDevices);
  const paginatedDevices = useMemo(() => {
    const start = page * itemsPerPage;
    const end = start + itemsPerPage;
    return filteredDevices.slice(start, end);
  }, [filteredDevices, page, itemsPerPage]);

  return (
    <div className="space-y-6">
      <DeviceFilters
        deviceType={deviceType}
        setDeviceType={setDeviceType}
        customerId={customerId}
        setCustomerId={setCustomerId}
        solutionName={solutionName}
        setSolutionName={setSolutionName}
        query={query}
        setQuery={setQuery}
      />

      <DeviceTable devices={paginatedDevices} />

      <DevicePagination
        page={page}
        setPage={setPage}
        totalItems={filteredDevices.length}
        itemsPerPage={itemsPerPage}
      />
    </div>
  );
}
