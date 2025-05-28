"use client";

import { useUserFormEdit } from "@/app/(main)/users/hooks/useUserFormEdit";
import { CommonFormContent } from "@/app/(main)/users/[id]/edit/_components/CommonFormContent";
import { AccessControlContent } from "@/app/(main)/users/[id]/edit/_components/AccessControlContent";
import { AccountControlContent } from "@/app/(main)/users/[id]/edit/_components/AccountControlContent";
import { UserCustomButton } from "@/app/(main)/users/_components/UserCustomButton";
import { User } from "@/types/user";

type Props = {
  accessToken: string;
  role: string;
  userId: string;
  user: User;
};
export default function UserEditForm({
  accessToken,
  role,
  userId,
  user,
}: Props) {
  const form = useUserFormEdit(accessToken, role, userId);
  const userLabel = `：${user.last_name} ${user.first_name}`;

  if (form.errorMessage) {
    return (
      <div className="flex flex-col gap-8">
        <div className="text-red-500 text-2xl">
          <p>{form.errorMessage}</p>
        </div>
      </div>
    );
  }
  return (
    <div>
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
              <AccountControlContent {...form} />
            </div>
          </div>
          <UserCustomButton {...form} mainUnit="保存" subUnit="キャンセル" />
        </form>
      </div>
    </div>
  );
}
