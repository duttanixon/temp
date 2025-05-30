"use client";

import Link from "next/link";
import { useState } from "react";
import { TabsNav } from "../_components/TabsNav";
import CustomerCreateForm from "./_components/CustomerCreateForm";

export default function AddCustomerPage() {
  const [activeTab, setActiveTab] = useState("basic");
  return (
    <div>
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
          <CustomerCreateForm activeTab={activeTab} />
        </section>
      </div>
    </div>
  );
}
