"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { CustomerForm } from "@/app/(main)//customers/_components/CustomerForm";
import { TabsNav } from "@/app/(main)/customers/_components/TabsNav";

type Props = {
  accessToken: string;
};
export default function CustomerEditPage({ accessToken }: Props) {
  const [activeTab, setActiveTab] = useState("basic");
  const params = useParams();
  const customerId = params?.id as string;

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
          <CustomerForm
            accessToken={accessToken}
            activeTab={activeTab}
            customerId={customerId}
          />
        </section>
      </div>
    </div>
  );
}
