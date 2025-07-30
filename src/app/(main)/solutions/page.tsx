"use client";

import SolutionPagination from "@/app/(main)/users/_components/Pagination";
import { Solution } from "@/types/solution";
import axios from "axios";
import { Plus } from "lucide-react";
import { useSession } from "next-auth/react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import SolutionFilters from "./_components/SolutionFilters";
import SolutionTable from "./_components/SolutionTable";

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
  const [query, setQuery] = useState("");
  const isAdmin = session?.user?.role === "ADMIN";
  const [page, setPage] = useState(0);
  const itemsPerPage = 10;

  useEffect(() => {
    if (!session?.accessToken) return;

    getSolutions(session.accessToken).then((result) => {
      setSolutions(result);
    });
  }, [session]);

  const filteredSolutions = useMemo(() => {
    const q = query.toLowerCase();
    return solutions.filter((solution) => {
      const matchesDeviceType =
        !deviceType || solution.compatibility.includes(deviceType);
      const matchesStatus = !status || solution.status === status;
      const matchesQuery = !q || solution.name.toLowerCase().includes(q);
      return matchesDeviceType && matchesStatus && matchesQuery;
    });
  }, [solutions, deviceType, status, query]);

  const paginatedSolutions = useMemo(() => {
    const start = page * itemsPerPage;
    const end = start + itemsPerPage;
    return filteredSolutions.slice(start, end);
  }, [filteredSolutions, page, itemsPerPage]);

  useEffect(() => {
    setPage(0);
  }, [deviceType, status, query]);
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-[#2C3E50]">ソリューション</h1>
        {isAdmin && (
          <Link href="/solutions/add">
            <button className="bg-green-600 hover:bg-green-700 text-white font-semibold px-4 py-2 rounded cursor-pointer">
              <div className="flex justify-center items-center gap-1">
                <Plus size={20} />
                ソリューションの作成
              </div>
            </button>
          </Link>
        )}
      </div>

      <SolutionFilters
        deviceType={deviceType}
        setDeviceType={setDeviceType}
        status={status}
        setStatus={setStatus}
        query={query}
        setQuery={setQuery}
      />

      <SolutionTable initialSolutions={paginatedSolutions} />

      <SolutionPagination
        page={page}
        setPage={setPage}
        totalItems={filteredSolutions.length}
        itemsPerPage={itemsPerPage}
      />
    </div>
  );
}
