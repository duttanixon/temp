"use client";

import { Device } from "@/types/device";
import { useMemo, useState } from "react";
import DeviceFilters from "../../../_components/DeviceFilters";
import DevicePagination from "../../../../users/_components/Pagination";
import { DeviceTable } from "./DeviceTable";

interface DeviceListProps {
  initialDevices: Device[];
}

export default function DeviceList({ initialDevices }: DeviceListProps) {
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