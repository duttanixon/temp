/*
* This component host all the devicetable based on application, common accross all application
*/


"use client";

import { Device } from "@/types/device";
import { Solution } from "@/types/solution";
import { useMemo, useState } from "react";
import DeviceFilters from "./DeviceFilters";
import DevicePagination from "../../users/_components/Pagination";
import { DeviceTable } from "./DeviceTable";

interface DeviceListProps {
  initialDevices: Device[];
  solution: Solution;
}

export default function DeviceList({ initialDevices, solution }: DeviceListProps) {
  const [deviceType, setDeviceType] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(0);
  const itemsPerPage = 10;

  const filteredDevices = useMemo(() => {
    return initialDevices.filter((device) => {
      const matchesDeviceType = !deviceType || device.device_type === deviceType;
      const matchesStatus = !status || device.status === status;
      return matchesDeviceType && matchesStatus;
    });
  }, [initialDevices, deviceType, status]);

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
        status={status}
        setStatus={setStatus}
      />

      <DeviceTable devices={paginatedDevices} solution={solution}/>

      <DevicePagination
        page={page}
        setPage={setPage}
        totalItems={filteredDevices.length}
        itemsPerPage={itemsPerPage}
      />
    </div>
  );
}