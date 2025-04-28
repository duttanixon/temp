import Link from "next/link";

import { CustomerForm } from "./_components/CustomerForm";

export default function AddCustomerPage() {
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
        <CustomerForm />
      </div>
    </div>
  );
}
