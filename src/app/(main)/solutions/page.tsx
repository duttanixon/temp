"use client";

import { useEffect, useState, useMemo } from "react";
import { useSession } from "next-auth/react";
import SolutionTable from "./_components/SolutionTable";
import SolutionFilters from "./_components/SolutionFilters";
import { Solution } from "@/types/solution";
import Link from "next/link";
import axios from "axios";

async function getSolutions(accessToken: string): Promise<Solution[]> {
  const apiUrl = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/solutions/admin`;

  try {
    const response = await axios.get<Solution[]>(apiUrl, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
      },
    });

    return response.data;
  } catch (error) {
    console.error("Error fetching solutions:", error);
    return [];
  }
}

export default function SolutionsPage() {
  const { data: session } = useSession();
  const [solutions, setSolutions] = useState<Solution[]>([]);
  const [deviceType, setDeviceType] = useState("");
  const [status, setStatus] = useState("");
  const isAdmin = session?.user?.role === "ADMIN";

  useEffect(() => {
    if (!session?.accessToken) return;

    getSolutions(session.accessToken).then((result) => {
      setSolutions(result);
    });
  }, [session]);

  const filteredSolutions = useMemo(() => {
    return solutions.filter((solution) => {
      const matchesDeviceType =
        !deviceType || solution.compatibility.includes(deviceType);
      const matchesStatus = !status || solution.status === status;
      return matchesDeviceType && matchesStatus;
    });
  }, [solutions, deviceType, status]);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-[#2C3E50]">
          ソリューション管理
        </h1>
        {isAdmin && (
          <Link
            href="/solutions/add"
            className="bg-[#27AE60] text-white py-2 px-4 rounded hover:bg-[#219955] transition-colors"
          >
            新規ソリューション追加
          </Link>
        )}
      </div>

      <SolutionFilters
        deviceType={deviceType}
        setDeviceType={setDeviceType}
        status={status}
        setStatus={setStatus}
      />

      <SolutionTable initialSolutions={filteredSolutions} />
    </div>
  );
}
