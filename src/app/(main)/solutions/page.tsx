// src/app/(main)/solutions/page.tsx
import { auth } from "@/auth";
import SolutionTable from "./_components/SolutionTable";
import SolutionFilters from "./_components/SolutionFilters";
import { solutionService } from "@/services/solutionService";
import Link from "next/link";

async function getSolutions(accessToken: string) {
  const apiUrl = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/solutions/admin`;

  try {
    const response = await fetch(apiUrl, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
      },
      cache: "no-store", // Disable caching to always get fresh data
    });
    if (!response.ok) {
      throw new Error(`Failed to fetch solutions: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error fetching solutions:", error);
    return [];
  }
}

export default async function SolutionsPage() {
  const session = await auth();
  const accessToken = session?.accessToken ?? "";
  const solutions = await getSolutions(accessToken);
  const isAdmin = session?.user?.role === "ADMIN";

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-[#2C3E50]">ソリューション管理</h1>
        {isAdmin && (
          <Link
            href="/solutions/add"
            className="bg-[#27AE60] text-white py-2 px-4 rounded hover:bg-[#219955] transition-colors"
          >
            新規ソリューション追加
          </Link>
        )}
      </div>

      <SolutionFilters />

      <SolutionTable initialSolutions={solutions} />
    </div>
  );
}