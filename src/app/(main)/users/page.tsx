import Link from "next/link";
import { auth } from "@/auth";

export default async function page() {
  // サーバーサイドでセッションを取得
  const session = await auth();
  console.log("👥 USERS PAGE: Session data:", session);
  return (
    <div className="flex flex-col">
      <h1 className="text-3xl font-bold underline">Users</h1>
      <Link href="/users/add">
        <button className="p-3 bg-blue-500 text-white rounded hover:bg-blue-600">
          作成
        </button>
      </Link>
    </div>
  );
}
