"use client";

import Link from "next/link";
import { CustomerForm } from "@/app/(main)/customers/_components/CustomerForm";

type Props = {
  accessToken: string;
};

export default function AddCustomerClient({ accessToken }: Props) {
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
          <CustomerForm accessToken={accessToken} />
        </section>
      </div>
    </div>
  );
}
