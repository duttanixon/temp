// HeaderContainer.tsx (Server Component)
import { auth } from "@/auth"; // 新しいimport
import { HeaderClient } from "./HeaderClient";

export async function Header() {
    // NextAuth v5のauth()関数を使用してセッション情報を取得
    const session = await auth();

    // ユーザー情報を抽出（変更なし）
    const userRole = session?.user?.role || "";
    const customerName = session?.user?.customerName || "Customer";
    const userName =
        `${session?.user?.firstName} ${session?.user?.lastName}` ||
        session?.user?.email?.split("@")[0] ||
        "";

    // サブヘッダーを表示するロール（変更なし）
    const subHeaderViewRoles = ["CUSTOMER_ADMIN", "CUSTOMER_USER"];
    // ユーザーロールに基づいてサブヘッダーを選択（変更なし）
    const isSubHeaderView = subHeaderViewRoles.includes(userRole);

    return (
        <HeaderClient
            userName={userName}
            customerName={customerName}
            isSubHeaderView={isSubHeaderView}
            isAuthenticated={!!session}
        />
    );
}
