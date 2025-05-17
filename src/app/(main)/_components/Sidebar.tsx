// components/Sidebar.tsx
import { auth } from "@/auth";
import { AdminSidebar } from "./AdminSidebar";
import { CustomerSidebar } from "./CustomerSidebar";

export const Sidebar = async () => {
  // NextAuth v5のauth()関数を使用してセッション情報を取得
  const session = await auth();
  const userRole = session?.user?.role || "";

  // Customer View を表示するロール
  const customerViewRoles = ["CUSTOMER_ADMIN"];

  // ユーザーロールに基づいてサイドバーを選択
  const isCustomerView = customerViewRoles.includes(userRole);

  return isCustomerView ? <CustomerSidebar /> : <AdminSidebar />;
};
