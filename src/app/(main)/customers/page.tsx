// File: app/(main)/customers/page.tsx
"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import CustomerTable from "./_components/CustomerTable";
import SearchFilters from "./_components/SearchFilters";
import StatsCard from "./_components/StatsCard";

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

  // useEffect(() => {
  //   const fetchCustomers = async () => {
  //     try {
  //       const res = await fetch("/api/customers?skip=3&limit=50");
  //       const data = await res.json();
  //       const list = Array.isArray(data)
  //         ? data
  //         : Array.isArray(data.customers)
  //           ? data.customers
  //           : Array.isArray(data.data)
  //             ? data.data
  //             : [];

  //       setAllCustomers(list);
  //       setFilteredCustomers(list);
  //     } catch (err) {
  //       console.error("Failed to fetch customers:", err);
  //     }
  //   };
  //   fetchCustomers();
  // }, []);

  useEffect(() => {
    const fetchAllCustomers = async () => {
      let allData: Customer[] = [];
      let skip = 0;
      const limit = 20;
      let hasMore = true;

      try {
        while (hasMore) {
          const res = await fetch(`/api/customers?skip=${skip}&limit=${limit}`);
          const data = await res.json();

          const list: Customer[] = Array.isArray(data)
            ? data
            : Array.isArray(data.customers)
              ? data.customers
              : Array.isArray(data.data)
                ? data.data
                : [];

          allData = [...allData, ...list];

          if (list.length < limit) {
            hasMore = false; // no more data to fetch
          } else {
            skip += limit; // move to the next batch
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

  const handleSearch = (query: string, status: string) => {
    let filtered = allCustomers;

    if (status !== "全ての状態") {
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

    setFilteredCustomers(filtered);
  };

  const total = allCustomers.length;
  const active = allCustomers.filter((c) => c.status === "ACTIVE").length;
  const devices = allCustomers.length;

  return (
    <div className="space-y-6 px-6 pt-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">顧客管理セクション</h1>
        <Link href="/customers/add">
          <button className="bg-green-600 hover:bg-green-700 text-white font-semibold px-4 py-2 rounded">
            + 顧客追加
          </button>
        </Link>
      </div>

      <SearchFilters onSearch={handleSearch} />

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

      <CustomerTable
        customers={filteredCustomers}
        page={page}
        setPage={setPage}
        itemsPerPage={10}
      />
    </div>
  );
}
