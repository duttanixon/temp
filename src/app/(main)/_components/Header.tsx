// HeaderContainer.tsx (Server Component)
import { getSessionData } from "@/lib/session";
import { HeaderClient } from "./HeaderClient";

export async function Header() {
  const { user, isAuthenticated } = await getSessionData();

  // ユーザー情報を抽出（変更なし）
  const userRole = user?.role || "";
  const customerName = user?.customerName || "Customer";
  const userName =
    `${user?.firstName || ""} ${user?.lastName || ""}`.trim() ||
    user?.email?.split("@")[0] ||
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
      isAuthenticated={isAuthenticated}
    />
  );
}
