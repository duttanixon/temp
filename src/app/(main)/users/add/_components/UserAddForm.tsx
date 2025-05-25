"use client";

import Link from "next/link";
import { useUserFormCreate } from "@/app/(main)/users/hooks/useUserFormCreate";
import { CommonFormContent } from "@/app/(main)/users/add/_components/CommonFormContent";
import { AdminFormContent } from "@/app/(main)/users/add/_components/AdminFormContent";
import { UserCustomButton } from "@/app/(main)/users/_components/UserCustomButton";
type Props = {
  accessToken: string;
  role: string;
  customer?: string;
};
export default function UserAddForm({ accessToken, role, customer }: Props) {
  const form = useUserFormCreate(accessToken, role);
  const customerLabel =
    role === "ADMIN" ? "" : role === "CUSTOMER_ADMIN" ? `：${customer}` : "";
  return (
    <div>
      <h2 className="text-sm text-[#7F8C8D]">
        <Link href={"/users"} className="hover:underline">
          ユーザー管理
        </Link>{" "}
        &gt; 新規ユーザー追加
      </h2>
      <div className="flex flex-col gap-8">
        <h1 className="text-2xl font-bold text-[#2C3E50]">
          新規ユーザー追加{customerLabel}
        </h1>
        <form onSubmit={form.handleSubmit} className="flex flex-col gap-4">
          <div className="w-170 h-145 border border-[#BDC3C7] rounded bg-[#FFFFFF]">
            <CommonFormContent {...form} />
            {role === "ADMIN" && (
              <AdminFormContent {...form} accessToken={accessToken} />
            )}
          </div>
          <UserCustomButton {...form} mainUnit="作成" subUnit="キャンセル" />
        </form>
      </div>
    </div>
  );
}
