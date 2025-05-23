import { auth } from "@/auth";
import { redirect } from "next/navigation";
import SolutionCreateForm from "../_components/SolutionCreateForm";

export default async function AddSolutionPage() {
  const session = await auth();
  const accessToken = session?.accessToken ?? "";
  const isAdmin = session?.user?.role === "ADMIN";

  if (!accessToken || !isAdmin) {
    redirect("/solutions");
  }

  return (
    <div className="space-y-6">
      <div>
        <a href="/solutions" className="text-sm text-[#7F8C8D] hover:underline">
          ソリューション管理
        </a>
        <h1 className="text-2xl font-bold text-[#2C3E50]">新規ソリューション追加</h1>
      </div>

      <SolutionCreateForm />
    </div>
  );
}