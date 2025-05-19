import { auth } from "@/auth";
import AddAdminUserForm from "@/app/(main)/users/add/_components/UserAddForm";
// import AddCustomerAdminUserForm from "@/app/(main)/users/add/_components/AddCustomerAdminUserForm";

export default async function AddUserPage() {
  // サーバーサイドでセッションを取得
  const session = await auth();
  const role = session?.user?.role;
  const accessToken = session?.accessToken ?? "";
  console.log("accessToken:", accessToken);
  console.log("typeof accessToken:", typeof accessToken);
  console.log("accessToken keys:", Object.keys(accessToken));

  console.log(" ADD USER PAGE: Session data:", session);
  if (role !== "ADMIN" && role !== "CUSTOMER_ADMIN") {
    return <div className="text-red-500">権限がありません</div>;
  }

  return (
    <div className="flex flex-col">
      <AddAdminUserForm accessToken={accessToken} role={role} />
    </div>
  );
}
