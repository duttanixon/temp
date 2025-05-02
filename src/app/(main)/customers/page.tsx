"use client";

import Link from "next/link";

export default function CustomerPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold">顧客管理</h1>
      <Link
        href="/customers/add"
        className="text-blue-600 underline hover:text-blue-800"
      >
        顧客追加
      </Link>
    </div>
  );
}
