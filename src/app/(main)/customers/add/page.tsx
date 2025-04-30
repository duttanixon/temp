"use client";

import { useState } from "react";
import Link from "next/link";
import { TabsNav } from "./_components/TabsNav";
import { CustomerForm } from "./_components/CustomerForm";

export default function AddCustomerPage() {
  const [activeTab, setActiveTab] = useState("basic");
  return (
    <div className="px-8 py-4">
      <h2 className="text-sm text-[#7F8C8D]">
        <Link href="/customers" className="hover:underline">
          顧客管理
        </Link>{" "}
        &gt; 新規顧客追加
      </h2>
      <div className="flex flex-col gap-8 text-2xl font-bold text-[#2C3E50]">
        新規顧客追加
        <section className="flex flex-col gap-4">
          <div className="inline-flex w-fit border border-[#BDC3C7] rounded bg-[#FFFFFF] overflow-hidden">
            <TabsNav activeTab={activeTab} onChange={setActiveTab} />
          </div>
          <CustomerForm activeTab={activeTab} />
        </section>
      </div>
    </div>
  );
}
