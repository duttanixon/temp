// HeaderContainer.tsx (Server Component)
import { authOptions } from "@/app/api/auth/[...nextauth]/route";
import { getServerSession } from "next-auth/next";
import { HeaderClient } from "./HeaderClient";

export async function Header() {
    // サーバーサイドでセッション情報を取得
    const session = await getServerSession(authOptions);

    // ユーザー情報を抽出
    const userRole = session?.user?.role || "";
    const customerName = session?.user?.customerName || "Tokyo Metro";
    const userName =
        session?.user?.name || session?.user?.email?.split("@")[0] || "";

    // サブヘッダーを表示するロール
    const subHeaderViewRoles = ["CUSTOMER_ADMIN", "CUSTOMER_USER"];
    // ユーザーロールに基づいてサブヘッダーを選択
    const isSubHeaderView = subHeaderViewRoles.includes(userRole);

    return (
        <HeaderClient
            userName={userName}
            userRole={userRole}
            customerName={customerName}
            isSubHeaderView={isSubHeaderView}
            isAuthenticated={!!session}
        />
    );
}
