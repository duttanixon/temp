/*
 * This component host all the devicetable based on application, common accross all application
 */

"use client";

import { Device } from "@/types/device";
import { Solution } from "@/types/solution";
import { useMemo, useState } from "react";
import DevicePagination from "../../users/_components/Pagination";
import SolutionDeviceFilters from "./SolutionDeviceFilters";
import { SolutionDeviceTable } from "./SolutionDeviceTable";

interface SolutionDeviceListProps {
  initialDevices: Device[];
  solution: Solution;
}

export default function SolutionDeviceList({
  initialDevices,
  solution,
}: SolutionDeviceListProps) {
  const [deviceType, setDeviceType] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(0);
  const [query, setQuery] = useState("");
  const itemsPerPage = 10;

  const filteredDevices = useMemo(() => {
    const q = query.toLowerCase();
    return initialDevices.filter((device) => {
      const matchesDeviceType =
        !deviceType || device.device_type === deviceType;
      const matchesStatus = !status || device.status === status;
      const matchesQuery = !q || device.name.toLowerCase().includes(q);
      return matchesDeviceType && matchesStatus && matchesQuery;
    });
  }, [initialDevices, deviceType, status, query]);

  const paginatedDevices = useMemo(() => {
    const start = page * itemsPerPage;
    const end = start + itemsPerPage;
    return filteredDevices.slice(start, end);
  }, [filteredDevices, page, itemsPerPage]);

  return (
    <div className="space-y-6">
      <SolutionDeviceFilters
        deviceType={deviceType}
        setDeviceType={setDeviceType}
        status={status}
        setStatus={setStatus}
        query={query}
        setQuery={setQuery}
      />

      <SolutionDeviceTable devices={paginatedDevices} solution={solution} />

      <DevicePagination
        page={page}
        setPage={setPage}
        totalItems={filteredDevices.length}
        itemsPerPage={itemsPerPage}
      />
    </div>
  );
}
