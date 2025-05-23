"use client";
import { useCallback, useState } from "react";
import Link from "next/link";

export default function CustomerOverviewPage() {
  const [customerId, setCustomerId] = useState("");
  const [error, setError] = useState("");

  const handleNavigate = useCallback(
    (e: React.MouseEvent<HTMLAnchorElement>) => {
      if (!customerId.trim()) {
        e.preventDefault();
        setError("CustomerIDを入力してください");
      } else {
        setError("");
      }
    },
    [customerId]
  );

  return (
    <div>
      <h2 className="text-sm text-[#7F8C8D]">
        <Link href="/customers" className="hover:underline">
          顧客管理
        </Link>{" "}
        &gt; 顧客概要
      </h2>
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-bold">顧客概要</h1>
        <div className="flex gap-4 items-center">
          <input
            type="text"
            placeholder="CustomerIDを入力"
            value={customerId}
            onChange={(e) => setCustomerId(e.target.value)}
            className="border"
          />
          <Link
            href={`${customerId}/edit`}
            onClick={handleNavigate}
            className=" text-blue-600 underline hover:text-blue-800"
          >
            顧客編集
          </Link>
        </div>
        {error && <p className="text-red-500 text-sm">{error}</p>}
      </div>
    </div>
  );
}
