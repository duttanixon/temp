"use client";

import { customerService } from "@/services/customerService";
import { Customer } from "@/types/customer";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import CustomerEditForm from "./_components/CustomerEditForm";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";

export default function AddCustomerPage() {
  const [customer, setCustomer] = useState<Customer | null>(null);
  const [loading, setLoading] = useState(true);

  const params = useParams();
  const customerId = params?.id as string;
  useEffect(() => {
    const fetchCustomer = async () => {
      try {
        setLoading(true);
        const customerData = await customerService.getCustomer(customerId);
        if (!customerData) {
          return <div>customerDataがありません</div>;
        }
        setCustomer(customerData);
      } catch (error) {
        console.error("Failed to fetch customer:", error);
        return <div>顧客情報の取得に失敗しました</div>;
      } finally {
        setLoading(false);
      }
    };

    if (customerId) {
      fetchCustomer();
    }
  }, [customerId]);

  // ローディング中の表示
  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-gray-600">読み込み中...</div>
      </div>
    );
  }
  if (!customer) {
    return <div>customerがありません</div>;
  }
  return (
    <div>
      <Breadcrumb className="text-sm text-[#7F8C8D]">
        <BreadcrumbList>
          <BreadcrumbItem className="hover:underline">
            <BreadcrumbLink href="/customers">顧客</BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator className="text-[#7F8C8D]" />
          <BreadcrumbItem className="hover:underline">
            <BreadcrumbLink href={`/customers/${customerId}`}>
              {customer?.name}
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator className="text-[#7F8C8D]" />
          <BreadcrumbItem>編集</BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
      <div className="flex flex-col gap-8 text-2xl font-bold text-[#2C3E50]">
        顧客編集
        <section className="flex flex-col gap-4">
          <CustomerEditForm customer={customer} />
        </section>
      </div>
    </div>
  );
}
