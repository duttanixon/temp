"use client";

import axios from "axios";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

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
  // setPage,
  itemsPerPage,
}: CustomerTableProps) {
  const [deviceCounts, setDeviceCounts] = useState<Record<string, number>>({});

  const router = useRouter();

  useEffect(() => {
    const fetchDeviceMap = async () => {
      try {
        const res = await axios.get("/api/customers/devices");
        const data = res.data;
        setDeviceCounts(data);
      } catch (error) {
        console.error("Error fetching device counts:", error);
      }
    };

    fetchDeviceMap();
  }, []);

  const paginated = [...customers]
    .sort(
      (a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )
    .slice(page * itemsPerPage, (page + 1) * itemsPerPage);
  // const totalItems = customers.length;

  return (
    <div className="overflow-x-auto rounded-lg border border-[#BDC3C7]">
      <table className="w-full min-w-[800px] divide-y divide-[#BDC3C7]">
        <colgroup>
          <col className="w-1/5" /> {/* 顧客名: 25% */}
          <col className="w-1/4" /> {/* メールアドレス: 40% */}
          <col className="w-1/10" /> {/* デバイス: 8% */}
          <col className="w-[15%]" /> {/* 状態: 15% */}
          <col className="w-[15%]" /> {/* 作成日: 10% */}
          <col className="w-[15%]" /> {/* アクション: 2% */}
        </colgroup>
        <thead className="bg-[#ECF0F1]">
          <tr>
            <th
              scope="col"
              className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50]">
              顧客名
            </th>
            <th
              scope="col"
              className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50]">
              メールアドレス
            </th>
            <th
              scope="col"
              className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50]">
              デバイス
            </th>
            <th
              scope="col"
              className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50]">
              状態
            </th>
            <th
              scope="col"
              className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50]">
              作成日
            </th>
            <th
              scope="col"
              className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50]">
              アクション
            </th>
          </tr>
        </thead>
        <tbody className="bg-white">
          {paginated.length > 0 ? (
            paginated.map((customer) => (
              <tr
                key={customer.customer_id}
                onClick={() =>
                  router.push(`/customers/${customer.customer_id}`)
                }
                className="border-t cursor-pointer hover:bg-[#F9F9F9] transition-colors duration-150 bg-white">
                <td className="px-6 py-3 text-sm text-[#2C3E50] max-w-0">
                  <div className="truncate">{customer.name}</div>
                </td>
                <td className="px-6 py-3 whitespace-nowrap text-sm text-[#2C3E50] max-w-0">
                  <div className="truncate">{customer.contact_email}</div>
                </td>
                <td className="px-6 py-3 whitespace-nowrap text-sm text-[#2C3E50] text-center">
                  {deviceCounts[customer.customer_id] ?? "0"}
                </td>
                <td className="px-6 py-3 whitespace-nowrap text-sm text-[#2C3E50] text-center">
                  <span
                    className={`px-2 py-1 rounded-full ${
                      customer.status === "ACTIVE"
                        ? "bg-green-100 text-green-700"
                        : customer.status === "INACTIVE"
                          ? "bg-yellow-100 text-yellow-700"
                          : "bg-gray-100 text-gray-700"
                    }`}>
                    {customer.status === "ACTIVE"
                      ? "アクティブ"
                      : customer.status === "INACTIVE"
                        ? "非アクティブ"
                        : "一時停止中"}
                  </span>
                </td>
                <td className="px-6 py-3 whitespace-nowrap text-sm text-[#2C3E50] text-center">
                  <span className="px-2 py-1 ">
                    {new Date(customer.created_at).toISOString().split("T")[0]}
                  </span>
                </td>
                <td className="px-6 py-3 whitespace-nowrap text-sm text-[#2C3E50] text-center">
                  <span className="px-2 py-1 ">-</span>
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td
                colSpan={6}
                className="px-6 py-4 text-center text-sm text-[#7F8C8D]">
                顧客が見つかりません
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
