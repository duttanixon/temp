"use client";
import axios from "axios";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import CustomerTable from "./_components/CustomerTable";
import SearchFilters from "./_components/SearchFilters";
import StatsCard from "./_components/StatsCard";
import CustomerPagination from "@/app/(main)/customers/_components/Pagination";

interface Customer {
  customer_id: string;
  name: string;
  contact_email: string;
  device: number;
  address: string;
  status: string;
  created_at: string;
}

export default function CustomersPage() {
  const [allCustomers, setAllCustomers] = useState<Customer[]>([]);
  const [filteredCustomers, setFilteredCustomers] = useState<Customer[]>([]);
  const [page, setPage] = useState(0);
  const [totalDevices, setTotalDevices] = useState(0);

  useEffect(() => {
    const fetchAllCustomers = async () => {
      let allData: Customer[] = [];
      let skip = 0;
      const limit = 20;
      let hasMore = true;

      try {
        while (hasMore) {
          const res = await axios.get(
            `/api/customers?skip=${skip}&limit=${limit}`
          );
          const data = res.data;

          const list: Customer[] = Array.isArray(data)
            ? data
            : Array.isArray(data.customers)
              ? data.customers
              : Array.isArray(data.data)
                ? data.data
                : [];

          allData = [...allData, ...list];

          if (list.length < limit) {
            hasMore = false;
          } else {
            skip += limit;
          }
        }

        setAllCustomers(allData);
        setFilteredCustomers(allData);
      } catch (err) {
        console.error("Failed to fetch all customers:", err);
      }
    };

    fetchAllCustomers();
  }, []);

  useEffect(() => {
    const fetchDeviceCounts = async () => {
      try {
        const res = await axios.get("/api/customers/devices", {
          headers: { Accept: "application/json" },
        });
        const data: Record<string, number> = res.data;

        const total = Object.values(data).reduce(
          (acc, count) => acc + count,
          0
        );
        setTotalDevices(total);
      } catch (error) {
        console.error("Failed to fetch device counts:", error);
      }
    };

    fetchDeviceCounts();
  }, []);

  const handleSearch = useCallback(
    (query: string, status: string) => {
      let filtered = allCustomers;

      if (status !== "すべて") {
        filtered = filtered.filter(
          (c) => c.status.toLowerCase() === status.toLowerCase()
        );
      }

      if (query) {
        const q = query.toLowerCase();
        filtered = filtered.filter(
          (c) =>
            c.name.toLowerCase().includes(q) ||
            c.contact_email.toLowerCase().includes(q)
        );
      }

      setPage(0);
      setFilteredCustomers(filtered);
    },
    [allCustomers]
  );

  const total = allCustomers.length;
  const active = allCustomers.filter((c) => c.status === "ACTIVE").length;
  const devices = totalDevices;
  const itemsPerPage = 10;
  const totalItems = filteredCustomers.length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">顧客管理</h1>
        <Link href="/customers/add">
          <button className="bg-green-600 hover:bg-green-700 text-white font-semibold px-12 py-2 rounded cursor-pointer">
            + 顧客追加
          </button>
        </Link>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatsCard title="すべての顧客" value={total} />
        <StatsCard
          title="アクティブ状態の顧客"
          value={active}
          colorClass="text-green-600"
        />
        <StatsCard
          title="すべてのデバイス"
          value={devices}
          colorClass="text-blue-600"
        />
      </div>

      <SearchFilters onSearch={handleSearch} />

      <CustomerTable
        customers={filteredCustomers}
        page={page}
        setPage={setPage}
        itemsPerPage={10}
      />

      <div className="">
        <CustomerPagination
          page={page}
          setPage={setPage}
          totalItems={totalItems}
          itemsPerPage={itemsPerPage}
        />
      </div>
    </div>
  );
}
