import Link from "next/link";

export default async function CustomerPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold">顧客管理</h1>
      <div className="flex flex-col gap-1">
        <Link
          href="/customers/add"
          className="text-blue-600 underline hover:text-blue-800"
        >
          顧客追加
        </Link>
        <Link
          href={"customers/${customer.id}"}
          className="text-blue-600 underline hover:text-blue-800"
        >
          顧客概要
        </Link>
      </div>
    </div>
  );
}
