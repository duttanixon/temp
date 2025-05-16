"use client";

import Link from "next/link";
import { useUserFormCreate } from "@/app/(main)/users/hooks/useUserFormCreate";
import { AddAdminUserContent } from "@/app/(main)/users/add/_components/AddAdminUserContent";
import { AddUserButton } from "@/app/(main)/users/add/_components/AddUserButton";
type Props = {
  accessToken: string;
};
export default function AddCustomerAdminUserForm({ accessToken }: Props) {
  const form = useUserFormCreate(accessToken, "CUSTOMER_ADMIN");
  console.log("---------:", accessToken);

  return (
    <div>
      <h2 className="text-sm text-[#7F8C8D]">
        <Link href="/users" className="hover:underline">
          管理
        </Link>{" "}
        &gt; 新規ユーザ追加
      </h2>
      <div className="flex flex-col gap-8">
        <h1 className="text-2xl font-bold text-[#2C3E50]">
          新規ユーザー追加：顧客管理者
        </h1>
        <form onSubmit={form.handleSubmit} className="flex flex-col gap-4">
          <div className="w-170 h-145 border border-[#BDC3C7] rounded bg-[#FFFFFF]">
            <AddAdminUserContent {...form} />
          </div>
          <AddUserButton {...form} />
        </form>
      </div>
    </div>
  );
}
