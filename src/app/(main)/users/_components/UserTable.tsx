"use client";

import { User } from "@/types/user";
import { ChevronDown, ChevronUp } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

// ユーザーと顧客名を組み合わせた型
interface UserWithCustomerName extends User {
  customer_name?: string;
}

interface UserTableProps {
  users: UserWithCustomerName[];
  page: number;
  setPage: (page: number) => void;
  itemsPerPage: number;
  userRole: string;
}

type SortKey =
  | "last_name"
  | "email"
  | "status"
  | "last_login"
  | "role"
  | "customer_name";
type SortOrder = "asc" | "desc";

export default function UserTable({
  users,
  page,
  setPage,
  itemsPerPage,
  userRole,
}: UserTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>("last_name");
  const [sortOrder, setSortOrder] = useState<SortOrder>("asc");
  const router = useRouter();

  const handleSort = (key: SortKey) => {
    if (key === sortKey) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortOrder("asc");
    }
    setPage(0);
  };

  const getSortedUsers = () => {
    return [...users].sort((a, b) => {
      const aVal = a[sortKey] ?? "";
      const bVal = b[sortKey] ?? "";
      if (typeof aVal === "string" && typeof bVal === "string") {
        return sortOrder === "asc"
          ? aVal.localeCompare(bVal)
          : bVal.localeCompare(aVal);
      }
      return 0;
    });
  };

  const paginated = getSortedUsers().slice(
    page * itemsPerPage,
    (page + 1) * itemsPerPage
  );

  const sortIcon = (key: SortKey) => {
    return sortKey === key ? (
      sortOrder === "asc" ? (
        <ChevronUp size={16} />
      ) : (
        <ChevronDown size={16} />
      )
    ) : null;
  };

  if (userRole === "CUSTOMER_ADMIN") {
    return (
      <div className="overflow-x-auto rounded-lg border border-[#BDC3C7]">
        <table className="w-full min-w-[800px]">
          <colgroup>
            <col className="w-1/5" />
            <col className="w-1/5" />
            <col className="w-1/5" />
            <col className="w-1/5" />
            <col className="w-1/5" />
          </colgroup>
          <thead className="bg-[#ECF0F1]">
            <tr>
              <th
                scope="col"
                onClick={() => handleSort("last_name")}
                className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50] cursor-pointer"
              >
                <div className="flex justify-center items-center gap-1 select-none whitespace-nowrap">
                  <div className="flex flex-col items-center">
                    <div>ユーザー名</div>
                    <div className="text-xs text-[#7F8C8D]">User Name</div>
                  </div>
                  {sortIcon("last_name")}
                </div>
              </th>
              <th
                scope="col"
                onClick={() => handleSort("email")}
                className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50] cursor-pointer"
              >
                <div className="flex justify-center items-center gap-1 select-none whitespace-nowrap">
                  <div className="flex flex-col items-center">
                    <div>メールアドレス</div>
                    <div className="text-xs text-[#7F8C8D]">Email Address</div>
                  </div>
                  {sortIcon("email")}
                </div>
              </th>
              <th
                scope="col"
                onClick={() => handleSort("status")}
                className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50] cursor-pointer"
              >
                <div className="flex justify-center items-center gap-1 select-none whitespace-nowrap">
                  <div className="flex flex-col items-center">
                    <div>状態</div>
                    <div className="text-xs text-[#7F8C8D]">Status</div>
                  </div>
                  {sortIcon("status")}
                </div>
              </th>
              <th
                scope="col"
                className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50]"
              >
                最終ログイン
                <div className="text-xs text-[#7F8C8D]">Last Login</div>
              </th>
              <th
                scope="col"
                className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50]"
              >
                <div className="absolute left-0 top-0 h-1/2 translate-y-1/2 border-l border-[#BDC3C7]" />
                アクション
                <div className="text-xs text-[#7F8C8D]">Actions</div>
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-[#BDC3C7]">
            {paginated.length > 0 ? (
              paginated.map((user) => (
                <tr
                  key={user.user_id}
                  onClick={() => router.push(`/users/${user.user_id}/edit`)}
                  className="border-t cursor-pointer hover:bg-[#F9F9F9] transition-colors duration-150 bg-white"
                >
                  {/* ユーザー名 */}
                  <td className="px-6 py-3 text-sm text-[#2C3E50] max-w-0">
                    <div className="truncate">
                      {user.last_name} {user.first_name}
                    </div>
                  </td>
                  {/* メールアドレス */}
                  <td className="px-6 py-3 whitespace-nowrap text-sm text-[#2C3E50] max-w-0">
                    <div className="truncate">{user.email}</div>
                  </td>

                  {/* 状態 */}
                  <td className="px-6 py-3 whitespace-nowrap text-sm text-[#2C3E50] text-center">
                    <span
                      className={`px-2 py-1 rounded-full ${
                        user.status === "ACTIVE"
                          ? "bg-green-100 text-green-700"
                          : user.status === "INACTIVE"
                            ? "bg-yellow-100 text-yellow-700"
                            : "bg-gray-100 text-gray-700"
                      }`}
                    >
                      {user.status === "ACTIVE"
                        ? "アクティブ"
                        : user.status === "INACTIVE"
                          ? "非アクティブ"
                          : "一時停止中"}
                    </span>
                  </td>
                  {/* 最終ログイン */}
                  <td className="px-6 py-3 whitespace-nowrap text-sm text-[#2C3E50] text-center">
                    <span className="px-2 py-1 ">{user.last_login}</span>
                  </td>
                  {/* アクション */}
                  <td className="relative px-6 py-3 whitespace-nowrap text-sm text-[#2C3E50] text-center">
                    <div className="absolute left-0 top-1/2 h-3/4 -translate-y-1/2 border-l border-[#BDC3C7]" />
                    <span className="px-2 py-1 ">-</span>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td
                  colSpan={5}
                  className="px-6 py-4 text-center text-sm text-[#7F8C8D]"
                >
                  ユーザーが見つかりません
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    );
  }
  return (
    <div className="overflow-x-auto rounded-lg border border-[#BDC3C7]">
      <table className="w-full min-w-[800px]">
        <colgroup>
          <col className="w-1/5" />
          <col className="w-1/5" />
          <col className="w-1/10" />
          <col className="w-1/5" />
          <col className="w-1/10" />
          <col className="w-1/10" />
          <col className="w-1/10" />
        </colgroup>
        <thead className="bg-[#ECF0F1] border-b border-[#BDC3C7]">
          <tr>
            <th
              scope="col"
              onClick={() => handleSort("last_name")}
              className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50] cursor-pointer"
            >
              <div className="flex justify-center items-center gap-1 select-none whitespace-nowrap">
                <div className="flex flex-col items-center">
                  <div>ユーザー名</div>
                  <div className="text-xs text-[#7F8C8D]">User Name</div>
                </div>
                {sortIcon("last_name")}
              </div>
            </th>
            <th
              scope="col"
              onClick={() => handleSort("email")}
              className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50] cursor-pointer"
            >
              <div className="flex justify-center items-center gap-1 select-none whitespace-nowrap">
                <div className="flex flex-col items-center">
                  <div>メールアドレス</div>
                  <div className="text-xs text-[#7F8C8D]">Email Address</div>
                </div>
                {sortIcon("email")}
              </div>
            </th>
            <th
              scope="col"
              onClick={() => handleSort("role")}
              className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50] cursor-pointer"
            >
              <div className="flex justify-center items-center gap-1 select-none whitespace-nowrap">
                <div className="flex flex-col items-center">
                  <div>権限</div>
                  <div className="text-xs text-[#7F8C8D]">Role</div>
                </div>
                {sortIcon("role")}
              </div>
            </th>
            <th
              scope="col"
              onClick={() => handleSort("customer_name")}
              className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50] cursor-pointer"
            >
              <div className="flex justify-center items-center gap-1 select-none whitespace-nowrap">
                <div className="flex flex-col items-center">
                  <div>顧客名</div>
                  <div className="text-xs text-[#7F8C8D]">Customer Name</div>
                </div>
                {sortIcon("customer_name")}
              </div>
            </th>
            <th
              scope="col"
              onClick={() => handleSort("status")}
              className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50] cursor-pointer"
            >
              <div className="flex justify-center items-center gap-1 select-none whitespace-nowrap">
                <div className="flex flex-col items-center">
                  <div>状態</div>
                  <div className="text-xs text-[#7F8C8D]">Status</div>
                </div>
                {sortIcon("status")}
              </div>
            </th>
            <th
              scope="col"
              className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50]"
            >
              最終ログイン
              <div className="text-xs text-[#7F8C8D]">Last Login</div>
            </th>
            <th
              scope="col"
              className="relative px-6 py-3 text-center text-sm font-semibold text-[#2C3E50]"
            >
              <div className="absolute left-0 top-0 h-1/2 translate-y-1/2 border-l border-[#BDC3C7]" />
              アクション
              <div className="text-xs text-[#7F8C8D]">Actions</div>
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-[#BDC3C7]">
          {paginated.length > 0 ? (
            paginated.map((user) => (
              <tr
                key={user.user_id}
                onClick={() => router.push(`/users/${user.user_id}/edit`)}
                className="border-t cursor-pointer hover:bg-[#F9F9F9] transition-colors duration-150 bg-white"
              >
                {/* ユーザー名 */}
                <td className="px-6 py-3 text-sm text-[#2C3E50] max-w-0">
                  <div className="truncate">
                    {user.last_name} {user.first_name}
                  </div>
                </td>
                {/* メールアドレス */}
                <td className="px-6 py-3 whitespace-nowrap text-sm text-[#2C3E50] max-w-0">
                  <div className="truncate">{user.email}</div>
                </td>
                {/* 権限 */}
                <td className="px-6 py-3 whitespace-nowrap text-sm text-[#2C3E50] text-center">
                  <span
                    className={`px-2 py-1 rounded-full ${
                      user.role === "ADMIN"
                        ? "bg-[#D6EAF8]  text-[#2980B9]"
                        : user.role === "CUSTOMER_ADMIN"
                          ? "bg-[#E6D9EC] text-[#8E44AD]"
                          : "bg-[#E5E8E8] text-[#7F8C8D]"
                    }`}
                  >
                    {user.role === "ADMIN"
                      ? "システム管理者"
                      : user.role === "CUSTOMER_ADMIN"
                        ? "顧客"
                        : "エンジニア"}
                  </span>
                </td>
                {/* 顧客名 */}
                <td className="px-6 py-3 whitespace-nowrap text-sm text-[#2C3E50] text-center">
                  <div className="truncate">{user.customer_name}</div>
                </td>
                {/* 状態 */}
                <td className="px-6 py-3 whitespace-nowrap text-sm text-[#2C3E50] text-center">
                  <span
                    className={`px-2 py-1 rounded-full ${
                      user.status === "ACTIVE"
                        ? "bg-green-100 text-green-700"
                        : user.status === "INACTIVE"
                          ? "bg-yellow-100 text-yellow-700"
                          : "bg-gray-100 text-gray-700"
                    }`}
                  >
                    {user.status === "ACTIVE"
                      ? "アクティブ"
                      : user.status === "INACTIVE"
                        ? "非アクティブ"
                        : "一時停止中"}
                  </span>
                </td>
                {/* 最終ログイン */}
                <td className="px-6 py-3 whitespace-nowrap text-sm text-[#2C3E50] text-center">
                  <span className="px-2 py-1 ">{user.last_login}</span>
                </td>
                {/* アクション */}
                <td className="relative px-6 py-3 whitespace-nowrap text-sm text-[#2C3E50] text-center">
                  <div className="absolute left-0 top-1/2 h-3/4 -translate-y-1/2 border-l border-[#BDC3C7]" />
                  <span className="px-2 py-1 ">-</span>
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td
                colSpan={7}
                className="px-6 py-4 text-center text-sm text-[#7F8C8D]"
              >
                ユーザーが見つかりません
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
