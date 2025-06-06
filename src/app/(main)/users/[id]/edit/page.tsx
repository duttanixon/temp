"use client";

import UserEditForm from "@/app/(main)/users/[id]/edit/_components/UserEditForm";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { userService } from "@/services/userService";
import { User } from "@/types/user";
import { useSession } from "next-auth/react";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

export default function UserEditPage() {
  const { data: session } = useSession();
  const role = session?.user?.role;
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const params = useParams();
  const userId = params?.id as string;

  useEffect(() => {
    const fetchUser = async () => {
      try {
        setLoading(true);
        const userData = await userService.getUser(userId);
        if (!userData) {
          return <div>ユーザーデータがありません</div>;
        }
        console.log("Fetched user data:", userData);
        setUser(userData);
      } catch (error) {
        console.error("ユーザー情報の取得に失敗しました:", error);

        return <div>ユーザー情報の取得に失敗しました</div>;
      } finally {
        setLoading(false);
      }
    };
    if (userId) {
      fetchUser();
    }
  }, [userId]);
  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-gray-600">読み込み中...</div>
      </div>
    );
  }
  if (!user) {
    return <h1>指定されたユーザーは存在しません</h1>;
  }
  const userLabel = `：${user?.last_name} ${user?.first_name}`;

  return (
    <div className="flex flex-col">
      <Breadcrumb className="text-sm text-[#7F8C8D]">
        <BreadcrumbList>
          <BreadcrumbItem className=" hover:underline">
            <BreadcrumbLink href="/users">ユーザー</BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator className="text-[#7F8C8D]" />
          <BreadcrumbItem>{`${user?.last_name} ${user?.first_name}`}</BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
      <div className="flex flex-col gap-8 w-170 text-2xl font-bold text-[#2C3E50]">
        ユーザー編集{userLabel}
        <section className="flex flex-col gap-4">
          {user && <UserEditForm role={role} user={user} />}
        </section>
      </div>
    </div>
  );
}
