"use client";

import { customerService } from "@/services/customerService";
import { Customer } from "@/types/customer";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { TabsNav } from "../../_components/TabsNav";
import CustomerEditForm from "./_components/CustomerEditForm";

export default function AddCustomerPage() {
  const [activeTab, setActiveTab] = useState("basic");
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
      <h2 className="text-sm text-[#7F8C8D]">
        <Link href="/customers" className="hover:underline">
          顧客管理
        </Link>{" "}
        &gt;{" "}
        <Link href={`/customers/${customerId}`} className="hover:underline">
          顧客概要
        </Link>{" "}
        &gt; 編集
      </h2>
      <div className="flex flex-col text-2xl font-bold text-[#2C3E50]">
        顧客編集
        <section className="flex flex-col gap-4">
          <h2 className="text-sm text-[#7F8C8D]">顧客ID: {customerId}</h2>
          <div className="inline-flex w-fit border border-[#BDC3C7] rounded bg-[#FFFFFF] overflow-hidden">
            <TabsNav activeTab={activeTab} onChange={setActiveTab} />
          </div>
          <CustomerEditForm activeTab={activeTab} customer={customer} />
        </section>
      </div>
    </div>
  );
}
