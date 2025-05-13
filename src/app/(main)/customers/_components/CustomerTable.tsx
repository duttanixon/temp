"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import CustomerPagination from "@/app/(main)/customers/_components/Pagination";
import axios from "axios";

interface Customer {
  customer_id: string;
  name: string;
  contact_email: string;
  address: string;
  device: number;
  status: string;
  created_at: string;
}

interface CustomerTableProps {
  customers: Customer[];
  page: number;
  setPage: (page: number) => void;
  itemsPerPage: number;
}

export default function CustomerTable({
  customers,
  page,
  setPage,
  itemsPerPage,
}: CustomerTableProps) {
  const router = useRouter();
  const [deviceCounts, setDeviceCounts] = useState<Record<string, number>>({});

  useEffect(() => {
    const fetchDeviceMap = async () => {
      try {
        const res = await axios.get("/api/customers/devices");
        const data = await res.data;
        setDeviceCounts(data);
      } catch (error) {
        console.error("Error fetching device counts:", error);
      }
    };

    fetchDeviceMap();
  }, []);

  const paginated = customers.slice(
    page * itemsPerPage,
    (page + 1) * itemsPerPage
  );
  const totalItems = customers.length;

  return (
    <div className="border  border-gray-400 rounded-md bg-white p-4 shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-[#ECF0F1] text-left">
            <tr>
              <th className="p-2">顧客名</th>
              <th className="p-2">連絡先メール</th>
              <th className="p-2 text-center">デバイス</th>
              <th className="p-2 text-center">状態</th>
              <th className="p-2 text-center">作成日</th>
              <th className="p-2 text-center">アクション</th>
            </tr>
          </thead>
          <tbody>
            {paginated.map((customer, index) => (
              <tr
                key={customer.customer_id}
                className={`border-t ${index % 2 === 0 ? "bg-white" : "bg-[#F9F9F9]"}`}
              >
                <td className="p-2">{customer.name}</td>
                <td className="p-2">{customer.contact_email}</td>
                <td className="p-2 text-center">
                  {deviceCounts[customer.customer_id] ?? "0"}
                </td>
                <td className="p-2 text-center">
                  <span
                    className={`text-xs font-medium px-2 py-1 rounded-full ${
                      customer.status === "ACTIVE"
                        ? "bg-green-100 text-green-700"
                        : customer.status === "INACTIVE"
                          ? "bg-yellow-100 text-yellow-700"
                          : "bg-gray-100 text-gray-700"
                    }`}
                  >
                    {customer.status === "ACTIVE"
                      ? "アクティブ"
                      : customer.status === "INACTIVE"
                        ? "非アクティブ"
                        : "一時停止中"}
                  </span>
                </td>
                <td className="p-2 text-center">
                  <span className="  text-xs font-medium px-2 py-1 ">
                    {new Date(customer.created_at).toISOString().split("T")[0]}
                  </span>
                </td>
                <td className="space-x-2 text-center">
                  <button
                    className="w-[55px] h-[25px] bg-[#2980B9]/20 text-[#2980B9] text-xs font-medium px-2 py-1 rounded"
                    onClick={() =>
                      router.push(
                        `/customers/customerDetails/${customer.customer_id}/edit`
                      )
                    }
                  >
                    編集
                  </button>
                  <button
                    className="w-[55px] h-[25px] bg-[#C0392B]/20 text-[#C0392B] text-xs font-medium px-2 py-1 rounded"
                    onClick={() =>
                      router.push(
                        `/customers/customerDetails/${customer.customer_id}`
                      )
                    }
                  >
                    閲覧
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination wrapped in card */}
      <div className="mt-10">
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
