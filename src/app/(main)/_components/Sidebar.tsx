import { getServerSession } from "next-auth";
// components/Sidebar.tsx
import { authOptions } from "@/app/api/auth/[...nextauth]/route";
import { AdminSidebar } from "./AdminSidebar";
import { CustomerSidebar } from "./CustomerSidebar";

export const Sidebar = async () => {
    // サーバーサイドでセッションを取得
    const session = await getServerSession(authOptions);
    const userRole = session?.user?.role || "";

    // Customer View を表示するロール
    const customerViewRoles = ["CUSTOMER_ADMIN", "CUSTOMER_USER"];

    // ユーザーロールに基づいてサイドバーを選択
    const isCustomerView = customerViewRoles.includes(userRole);

    return isCustomerView ? <CustomerSidebar /> : <AdminSidebar />;
};
