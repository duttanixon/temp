import Link from "next/link";
import { auth } from "@/auth";

export default async function page() {
  // サーバーサイドでセッションを取得
  const session = await auth();
  console.log("👥 USERS PAGE: Session data:", session);
  return (
    <div className="flex flex-col gap-2">
      <h1 className="text-3xl font-bold underline">Users</h1>
      <div className="flex flex-col text-blue-600 underline hover:text-blue-800">
        <Link href={"/users/add"}>作成</Link>
        <Link href={"users/${user.id}"}>編集</Link>
      </div>
    </div>
  );
}
