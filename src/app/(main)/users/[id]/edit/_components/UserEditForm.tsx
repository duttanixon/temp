"use client";

import Link from "next/link";
import { useUserFormEdit } from "@/app/(main)/users/hooks/useUserFormEdit";
import { CommonFormContent } from "@/app/(main)/users/[id]/edit/_components/CommonFormContent";
import { AccessControlContent } from "@/app/(main)/users/[id]/edit/_components/AccessControlContent";
import { AccountStatusContent } from "@/app/(main)/users/[id]/edit/_components/AccountStatusContent";
import { UserCustomButton } from "@/app/(main)/users/_components/UserCustomButton";

type Props = {
  accessToken: string;
  role: string;
  userId: string;
};
export default function UserEditForm({ accessToken, role, userId }: Props) {
  const form = useUserFormEdit(accessToken, role, userId);
  const userLabel = `：${form.firstName} ${form.lastName}`;
  return (
    <div>
      <h2 className="text-sm text-[#7F8C8D]">
        <Link href={"/users"} className="hover:underline">
          ユーザー管理
        </Link>{" "}
        &gt; ユーザー編集
      </h2>
      <div className="flex flex-col gap-8">
        <h1 className="text-2xl font-bold text-[#2C3E50]">
          ユーザー編集{userLabel}
        </h1>
        <form onSubmit={form.handleSubmit} className="flex flex-col gap-4">
          <div className="w-170 h-145 border border-[#BDC3C7] rounded bg-[#FFFFFF] p-4">
            <div className="flex flex-col gap-4">
              <CommonFormContent {...form} />
              {role === "ADMIN" && (
                <AccessControlContent {...form} accessToken={accessToken} />
              )}
              <AccountStatusContent {...form} />
            </div>
          </div>
          <UserCustomButton {...form} mainUnit="保存" subUnit="キャンセル" />
        </form>
      </div>
    </div>
  );
}
