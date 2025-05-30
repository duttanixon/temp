import { auth } from "@/auth";
import UserCreateForm from "@/app/(main)/users/add/_components/UserCreateForm";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";

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
  const customerLabel =
    role === "ADMIN" ? "" : role === "CUSTOMER_ADMIN" ? `：${customer}` : "";

  return (
    <div className="flex flex-col">
      <Breadcrumb className="text-sm text-[#7F8C8D]">
        <BreadcrumbList>
          <BreadcrumbItem className=" hover:underline">
            <BreadcrumbLink href="/users">ユーザー</BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator className="text-[#7F8C8D]" />
          <BreadcrumbItem>ユーザーの作成</BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
      <div className="flex flex-col gap-8 w-170 text-2xl font-bold text-[#2C3E50]">
        ユーザーの作成{customerLabel}
        <section className="flex flex-col gap-4">
          <UserCreateForm role={role} />
        </section>
      </div>
    </div>
  );
}
