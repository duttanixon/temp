import { auth } from "@/auth";
import UserAddForm from "@/app/(main)/users/add/_components/UserAddForm";

export default async function AddUserPage() {
  // サーバーサイドでセッションを取得
  const session = await auth();
  const role = session?.user?.role;
  const accessToken = session?.accessToken ?? "";
  const customer = session?.user?.customerName;
  console.log("accessToken:", accessToken);
  console.log("typeof accessToken:", typeof accessToken);
  console.log("accessToken keys:", Object.keys(accessToken));
  console.log("session:", session);

  console.log(" ADD USER PAGE: Session data:", session);
  if (role !== "ADMIN" && role !== "CUSTOMER_ADMIN") {
    return <div className="text-red-500">権限がありません</div>;
  }

  return (
    <div className="flex flex-col">
      <UserAddForm accessToken={accessToken} role={role} customer={customer} />
    </div>
  );
}
