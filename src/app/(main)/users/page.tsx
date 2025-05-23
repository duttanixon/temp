import Link from "next/link";
import { auth } from "@/auth";
import UserEditSearch from "@/app/(main)/users/_components/UserEditSearch";

export default async function page() {
  // サーバーサイドでセッションを取得
  const session = await auth();
  console.log("👥 USERS PAGE: Session data:", session);
  return (
    <div className="flex flex-col gap-2">
      <h2 className="text-sm text-[#7F8C8D]">
        <Link href="/users" className="hover:underline">
          ユーザー管理
        </Link>{" "}
        &gt;
      </h2>
      <h1 className="text-2xl font-bold">ユーザー管理</h1>
      <div className="text-blue-600 underline hover:text-blue-800">
        <Link href={"/users/add"}>作成</Link>
      </div>
      <UserEditSearch />
    </div>
  );
}
