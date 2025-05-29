"use client";

import CustomerCreateForm from "./_components/CustomerCreateForm";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";

export default function AddCustomerPage() {
  return (
    <div>
      <Breadcrumb className="text-sm text-[#7F8C8D]">
        <BreadcrumbList>
          <BreadcrumbItem className=" hover:underline">
            <BreadcrumbLink href="/customers">顧客</BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator className="text-[#7F8C8D]" />
          <BreadcrumbItem>顧客の作成</BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
      <div className="flex flex-col gap-8 text-2xl font-bold text-[#2C3E50]">
        顧客の作成
        <section className="flex flex-col gap-4">
          <CustomerCreateForm />
        </section>
      </div>
    </div>
  );
}
