"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { CustomerForm } from "@/app/(main)//customers/_components/CustomerForm";

type Props = {
  accessToken: string;
};
export default function CustomerEditPage({ accessToken }: Props) {
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
          <CustomerForm accessToken={accessToken} customerId={customerId} />
        </section>
      </div>
    </div>
  );
}
