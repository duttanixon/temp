"use client";

import UserCreateForm from "@/app/(main)/users/add/_components/UserCreateForm";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { useSession } from "next-auth/react";

export default function AddUserPage() {
  const { data: session } = useSession();
  const role = session?.user?.role;
  const customer = session?.user?.customerName;

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
          <UserCreateForm
            role={role as "ADMIN" | "ENGINEER" | "CUSTOMER_ADMIN"}
          />
        </section>
      </div>
    </div>
  );
}
