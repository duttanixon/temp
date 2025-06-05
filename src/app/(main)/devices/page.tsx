"use client";

import { useEffect, useState, useMemo } from "react";
import { useSession } from "next-auth/react";
import { Device } from "@/types/device";
import DeviceTable from "./_components/DeviceTable";
import DeviceFilters from "./_components/DeviceFilters";
import Link from "next/link";
import axios from "axios";
import DevicePagination from "../users/_components/Pagination";

async function getDevices(accessToken: string): Promise<Device[]> {
  const apiUrl = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/devices`;

  try {
    const response = await axios.get<Device[]>(apiUrl, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
      },
    });

    return response.data;
  } catch (error) {
    console.error("Error fetching devices:", error);
    return [];
  }
}

export default function DevicesPage() {
  const { data: session } = useSession();
  const [devices, setDevices] = useState<Device[]>([]);
  const [deviceType, setDeviceType] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(0);
  const itemsPerPage = 10;

  useEffect(() => {
    if (!session?.accessToken) return;

    getDevices(session.accessToken).then((result) => {
      setDevices(result);
    });
  }, [session]);

  const filteredDevices = useMemo(() => {
    const filtered = devices.filter((device) => {
      const matchesDeviceType =
        !deviceType || device.device_type === deviceType;
      const matchesStatus = !status || device.status === status;
      return matchesDeviceType && matchesStatus;
    });

    return filtered;
  }, [devices, deviceType, status]);

  const paginatedDevices = useMemo(() => {
    const start = page * itemsPerPage;
    const end = start + itemsPerPage;
    return filteredDevices.slice(start, end);
  }, [filteredDevices, page, itemsPerPage]);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-[#2C3E50]">デバイス管理</h1>
        <Link
          href="/devices/add"
          className="bg-[#27AE60] text-white py-2 px-4 rounded hover:bg-[#219955] transition-colors"
        >
          新規デバイス追加
        </Link>
      </div>

      <DeviceFilters
        deviceType={deviceType}
        setDeviceType={setDeviceType}
        status={status}
        setStatus={setStatus}
      />

      <DeviceTable initialDevices={paginatedDevices} />

      <DevicePagination
        page={page}
        setPage={setPage}
        totalItems={filteredDevices.length}
        itemsPerPage={itemsPerPage}
      />
    </div>
  );
}
