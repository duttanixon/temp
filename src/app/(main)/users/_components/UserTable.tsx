"use client";

import { User } from "@/types/user";
import { useRouter } from "next/navigation";

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

export default function UserTable({
  users,
  page,
  // setPage,
  itemsPerPage,
  userRole,
}: UserTableProps) {
  const router = useRouter();

  const paginated = [...users]
    .sort(
      (a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )
    .slice(page * itemsPerPage, (page + 1) * itemsPerPage);
  // const totalItems = users.length;

  if (userRole === "CUSTOMER_ADMIN") {
    return (
      <div className="overflow-x-auto rounded-lg border border-[#BDC3C7]">
        <table className="w-full min-w-[800px] divide-y divide-[#BDC3C7]">
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
                className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50]">
                ユーザー名
              </th>
              <th
                scope="col"
                className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50]">
                メールアドレス
              </th>
              <th
                scope="col"
                className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50]">
                状態
              </th>
              <th
                scope="col"
                className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50]">
                最終ログイン
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
              paginated.map((user) => (
                <tr
                  key={user.user_id}
                  onClick={() => router.push(`/users/${user.user_id}/edit`)}
                  className="border-t cursor-pointer hover:bg-[#F9F9F9] transition-colors duration-150 bg-white">
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
                      }`}>
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
                  <td className="px-6 py-3 whitespace-nowrap text-sm text-[#2C3E50] text-center">
                    <span className="px-2 py-1 ">-</span>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td
                  colSpan={5}
                  className="px-6 py-4 text-center text-sm text-[#7F8C8D]">
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
              className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50]">
              ユーザー名
            </th>
            <th
              scope="col"
              className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50]">
              メールアドレス
            </th>
            <th
              scope="col"
              className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50]">
              権限
            </th>
            <th
              scope="col"
              className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50]">
              顧客名
            </th>
            <th
              scope="col"
              className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50]">
              状態
            </th>
            <th
              scope="col"
              className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50]">
              最終ログイン
            </th>
            <th
              scope="col"
              className="px-6 py-3 text-center text-sm font-semibold text-[#2C3E50]">
              アクション
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-[#BDC3C7]">
          {paginated.length > 0 ? (
            paginated.map((user) => (
              <tr
                key={user.user_id}
                onClick={() => router.push(`/users/${user.user_id}/edit`)}
                className="border-t cursor-pointer hover:bg-[#F9F9F9] transition-colors duration-150 bg-white">
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
                    }`}>
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
                    }`}>
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
                <td className="px-6 py-3 whitespace-nowrap text-sm text-[#2C3E50] text-center">
                  <span className="px-2 py-1 ">-</span>
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td
                colSpan={7}
                className="px-6 py-4 text-center text-sm text-[#7F8C8D]">
                ユーザーが見つかりません
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
