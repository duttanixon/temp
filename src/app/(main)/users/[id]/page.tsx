"use client";
import { useState } from "react";
import Link from "next/link";

export default function UserOverviewPage() {
  const [userId, setUserId] = useState("");
  const [error, setError] = useState("");

  const handleNavigate = (e: React.MouseEvent<HTMLAnchorElement>) => {
    if (!userId.trim()) {
      e.preventDefault();
      setError("UserIDを入力してください");
    } else {
      setError("");
    }
  };

  return (
    <div>
      <h2 className="text-sm text-[#7F8C8D]">
        <Link href="/users" className="hover:underline">
          ユーザー管理
        </Link>{" "}
        &gt; ユーザー概要
      </h2>
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-bold">ユーザー概要</h1>
        <div className="flex gap-4 items-center">
          <input
            type="text"
            placeholder="UserIDを入力"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            className="border"
          />
          <Link
            href={`${userId}/edit`}
            onClick={handleNavigate}
            className=" text-blue-600 underline hover:text-blue-800"
          >
            ユーザー編集
          </Link>
        </div>
        {error && <p className="text-red-500 text-sm">{error}</p>}
      </div>
    </div>
  );
}
