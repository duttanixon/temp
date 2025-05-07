"use client";

import CustomerPagination from "@/app/(main)/customers/_components/Pagination";
import { useRouter } from "next/navigation";

interface Customer {
    customer_id: string;
    name: string;
    contact_email: string;
    address: string;
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

    const paginated = customers.slice(
        page * itemsPerPage,
        (page + 1) * itemsPerPage
    );
    const totalItems = customers.length;

    return (
        <div className="space-y-4">
            <div className="border rounded overflow-x-auto">
                <table className="w-full text-sm">
                    <thead className="bg-gray-100 text-left">
                        <tr>
                            <th className="p-2">顧客名</th>
                            <th className="p-2">連絡先メール</th>
                            <th className="p-2">地球</th>
                            {/* <th className="p-2">デバイス</th> */}
                            <th className="p-2">ステータス</th>
                            <th className="p-2">作成日</th>
                            <th className="p-2">アクション</th>
                        </tr>
                    </thead>
                    <tbody>
                        {paginated.map((customer) => (
                            <tr className="border-t" key={customer.customer_id}>
                                <td className="p-2">{customer.name}</td>
                                <td>{customer.contact_email}</td>
                                <td>{customer.address}</td>
                                <td>
                                    <span
                                        className={`text-xs font-medium px-2 py-1 rounded-full ${
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
                                <td>
                                    <span className="bg-gray-100 text-gray-800 text-xs font-medium px-2 py-1 rounded-full">
                                        {new Date(
                                            customer.created_at
                                        ).toLocaleDateString()}
                                    </span>
                                </td>
                                <td className="space-x-2">
                                    <button
                                        className="bg-blue-100 text-blue-700 text-xs font-medium px-2 py-1 rounded"
                                        onClick={() =>
                                            router.push(
                                                `/customers/customerDetails/${customer.customer_id}/edit`
                                            )
                                        }>
                                        編集
                                    </button>
                                    <button
                                        className="bg-red-100 text-red-700 text-xs font-medium px-2 py-1 rounded"
                                        onClick={() =>
                                            router.push(
                                                `/customers/customerDetails/${customer.customer_id}`
                                            )
                                        }>
                                        表示
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            <CustomerPagination
                page={page}
                setPage={setPage}
                totalItems={totalItems}
                itemsPerPage={itemsPerPage}
            />
        </div>
    );
}
