"use client";
import UserPagination from "@/app/(main)/users/_components/Pagination";
import { customerService } from "@/services/customerService";
import { userService } from "@/services/userService";
import { User } from "@/types/user";
import { useSession } from "next-auth/react";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import SearchFilters from "./_components/SearchFilters";
import StatsCard from "./_components/StatsCard";
import UserTable from "./_components/UserTable";

// ユーザーと顧客名を組み合わせた型
interface UserWithCustomerName extends User {
  customer_name?: string;
}

// 顧客情報の型
interface Customer {
  id: string;
  name: string;
}
// カスタマーサービスのレスポンス型
interface CustomerResponse {
  customer_id?: string;
  id?: string;
  name?: string;
  customer_name?: string;
}
export default function UsersPage() {
  const { data: session, status } = useSession();
  const [allUsers, setAllUsers] = useState<UserWithCustomerName[]>([]);
  const [loading, setLoading] = useState(true);
  const [filteredUsers, setFilteredUsers] = useState<UserWithCustomerName[]>(
    []
  );
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [currentCustomerName, setCurrentCustomerName] = useState<string>("");
  const [page, setPage] = useState(0);

  // sessionから必要な値のみを抽出して安定化
  const userId = session?.user?.id;
  const userRole = session?.user?.role;
  const customerId = session?.user?.customerId;

  useEffect(() => {
    // セッションがロード中の場合は処理しない
    if (status === "loading") {
      return;
    }

    // 認証済み状態でない場合は処理しない（重要：これによりログアウト時の処理を防ぐ）
    if (status !== "authenticated") {
      setLoading(false);
      return;
    }

    const fetchUsersWithCustomerNames = async () => {
      try {
        setLoading(true);
        // セッションからユーザー情報を取得
        const currentUser = {
          user_id: userId,
          role: userRole,
          customer_id: customerId,
        };
        // 権限に応じてユーザーデータを取得
        let userData: User[];
        let allCustomersData: CustomerResponse[] = [];

        if (currentUser.role === "ADMIN") {
          // ADMINの場合：全ユーザーと全カスタマーを取得
          [userData, allCustomersData] = await Promise.all([
            userService.getUsers(),
            customerService.getCustomers(),
          ]);
        } else if (
          currentUser.role === "CUSTOMER_ADMIN" &&
          currentUser.customer_id
        ) {
          // CUSTOMER_ADMINの場合：自分のカスタマーのユーザーのみ取得
          userData = await userService.getUsers(currentUser.customer_id);

          // 顧客名を取得
          try {
            const customerInfo = await customerService.getCustomer(
              currentUser.customer_id
            );
            setCurrentCustomerName(customerInfo?.name || "");
          } catch (error) {
            console.error("Failed to fetch customer name:", error);
          }
        } else {
          // その他の権限の場合は空の配列
          userData = [];
        }

        if (!userData) {
          console.error("ユーザーデータが取得できませんでした");
          return;
        }

        // カスタマーデータの準備
        let customerData: Customer[] = [];
        let customerMap = new Map();

        if (currentUser.role === "ADMIN") {
          // ADMINの場合：すべてのカスタマー
          if (allCustomersData) {
            customerData = allCustomersData.map(
              (customer: CustomerResponse) => ({
                id: customer.customer_id || customer.id || "",
                name: customer.name || customer.customer_name || "",
              })
            );
            customerMap = new Map(customerData.map((c) => [c.id, c.name]));
          }
        } else if (
          currentUser.role === "CUSTOMER_ADMIN" &&
          currentUser.customer_id
        ) {
          // CUSTOMER_ADMINの場合：自分のカスタマーのみ
          try {
            const customerInfo = await customerService.getCustomer(
              currentUser.customer_id
            );
            if (customerInfo) {
              customerData = [
                {
                  id: currentUser.customer_id,
                  name: customerInfo.name || customerInfo.name || "",
                },
              ];
              customerMap = new Map([
                [
                  currentUser.customer_id,
                  customerInfo.name || customerInfo.name || "",
                ],
              ]);
            }
          } catch (error) {
            console.error("Failed to fetch customer info:", error);
            customerMap = new Map([
              [currentUser.customer_id, currentUser.customer_id],
            ]);
          }
        }

        // ユーザーデータに顧客名を追加
        const usersWithCustomerNames: UserWithCustomerName[] = userData.map(
          (user) => ({
            ...user,
            customer_name:
              customerMap.get(user.customer_id) || user.customer_id,
          })
        );

        setAllUsers(usersWithCustomerNames);
        setFilteredUsers(usersWithCustomerNames);
        setCustomers(customerData);
      } catch (error) {
        console.error("Failed to fetch users:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchUsersWithCustomerNames();
  }, [status, userId, userRole, customerId]); // currentUserオブジェクトを依存配列に追加

  const handleSearch = useCallback(
    (query: string, status: string, role: string, customer: string) => {
      let filtered = allUsers;

      if (status !== "すべて") {
        filtered = filtered.filter(
          (c) => c.status.toLowerCase() === status.toLowerCase()
        );
      }
      if (role !== "すべて") {
        filtered = filtered.filter(
          (c) => c.role.toLowerCase() === role.toLowerCase()
        );
      }
      if (customer !== "すべて") {
        filtered = filtered.filter(
          (c) => c.customer_name?.toLowerCase() === customer.toLowerCase()
        );
      }

      if (query) {
        const q = query.toLowerCase();
        filtered = filtered.filter(
          (c) =>
            c.last_name?.toLowerCase().includes(q) ||
            c.first_name?.toLowerCase().includes(q) ||
            c.email.toLowerCase().includes(q)
        );
      }

      setPage(0);
      setFilteredUsers(filtered);
    },
    [allUsers]
  );

  const total = allUsers.length;
  const active = allUsers.filter((c) => c.status === "ACTIVE").length;
  const itemsPerPage = 10;
  const totalItems = filteredUsers.length;

  // ローディング中の表示
  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-gray-600">読み込み中...</div>
      </div>
    );
  }
  // タイトルの決定
  const getTitle = () => {
    if (session?.user.role === "CUSTOMER_ADMIN" && currentCustomerName) {
      return `ユーザー管理：${currentCustomerName}`;
    }
    return "ユーザー管理";
  };
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">{getTitle()}</h1>
        <Link href="/users/add">
          <button className="bg-green-600 hover:bg-green-700 text-white font-semibold px-12 py-2 rounded cursor-pointer">
            + ユーザー追加
          </button>
        </Link>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatsCard title="すべてのユーザー" value={total} />
        <StatsCard
          title="アクティブ状態のユーザー"
          value={active}
          colorClass="text-green-600"
        />
      </div>

      <SearchFilters
        onSearch={handleSearch}
        customers={customers}
        userRole={userRole || "CUSTOMER_ADMIN"}
      />

      <UserTable
        users={filteredUsers}
        page={page}
        setPage={setPage}
        itemsPerPage={10}
        userRole={userRole || "CUSTOMER_ADMIN"}
      />

      <div>
        <UserPagination
          page={page}
          setPage={setPage}
          totalItems={totalItems}
          itemsPerPage={itemsPerPage}
        />
      </div>
    </div>
  );
}
