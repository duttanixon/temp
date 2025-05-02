"use client";

import Link from "next/link";
import { useState } from "react";
// import { useSession } from "next-auth/react";
import { CustomerForm } from "../_components/CustomerForm";
import { TabsNav } from "../_components/TabsNav";

type Props = {
  accessToken: string;
};

export default function AddCustomerClient({ accessToken }: Props) {
  const [activeTab, setActiveTab] = useState("basic");
  // const { data: session } = useSession();

  // const accessToken = session?.accessToken ?? "";
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
          <CustomerForm accessToken={accessToken} activeTab={activeTab} />
        </section>
      </div>
    </div>
  );
}
