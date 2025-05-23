import UserEditForm from "@/app/(main)/users/[id]/edit/_components/UserEditForm";
import { auth } from "@/auth";

type Props = {
  params: Promise<{
    id: string;
  }>;
};
export default async function UserEditPage(props: Props) {
  const params = await props.params;
  // サーバーサイドでセッションを取得
  const session = await auth();
  const role = session?.user?.role;
  const accessToken = session?.accessToken ?? "";
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
      <UserEditForm accessToken={accessToken} role={role} userId={params.id} />
    </div>
  );
}
