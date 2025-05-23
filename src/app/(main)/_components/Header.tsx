import { getSessionData } from "@/lib/session";
import { HeaderClient } from "./HeaderClient";

export async function Header() {
  const { user, isAuthenticated } = await getSessionData();

  // Extract user information
  const userInfo = {
    name:
      `${user?.firstName || ""} ${user?.lastName || ""}`.trim() ||
      user?.email?.split("@")[0] ||
      "",
    customerName: user?.customerName || "Customer",
  };

  // Determine whether to show customer-specific sub-header
  const showCustomerHeader = user?.role === "CUSTOMER_ADMIN";

  return (
    <HeaderClient
      userName={userInfo.name}
      customerName={userInfo.customerName}
      showCustomerHeader={showCustomerHeader}
      isAuthenticated={isAuthenticated}
    />
  );
}
