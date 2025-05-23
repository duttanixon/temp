"use client";
import { useCallback, useState } from "react";
import Link from "next/link";

export default function UserEditSearch() {
  const [userId, setUserId] = useState("");
  const [error, setError] = useState("");

  const handleNavigate = useCallback(
    (e: React.MouseEvent<HTMLAnchorElement>) => {
      if (!userId.trim()) {
        e.preventDefault();
        setError("UserIDを入力してください");
      } else {
        setError("");
      }
    },
    [userId]
  );

  return (
    <div>
      <div className="flex gap-4 items-center">
        <input
          type="text"
          placeholder="UserIDを入力"
          value={userId}
          onChange={(e) => setUserId(e.target.value)}
          className="border"
        />
        <Link
          href={`users/${userId}/edit`}
          onClick={handleNavigate}
          className=" text-blue-600 underline hover:text-blue-800"
        >
          ユーザー編集
        </Link>
      </div>
      {error && <p className="text-red-500 text-sm">{error}</p>}
    </div>
  );
}
