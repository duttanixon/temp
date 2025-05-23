// src/app/(main)/solutions/[solutionId]/edit/page.tsx
import { auth } from "@/auth";
import { notFound, redirect } from "next/navigation";
import SolutionEditForm from "../../_components/SolutionEditForm";

async function getSolution(solutionId: string, accessToken: string) {
  try {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/solutions/${solutionId}`,
      {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
        cache: "no-store",
      }
    );

    if (response.status === 404) {
      return null;
    }

    if (!response.ok) {
      throw new Error(`Failed to fetch solution: ${response.status}`);
    }

    return response.json();
  } catch (error) {
    console.error("Error fetching solution:", error);
    throw error;
  }
}

type Props = {
  params: Promise<{ solutionId: string }>;
};

export default async function EditSolutionPage({ params }: Props) {
  const resolvedParams = await params;
  const session = await auth();
  const accessToken = session?.accessToken ?? "";
  const solutionId = resolvedParams.solutionId;
  const isAdmin = session?.user?.role === "ADMIN";

  if (!accessToken || !isAdmin) {
    redirect("/solutions");
  }

  const solution = await getSolution(solutionId, accessToken);

  if (!solution) {
    notFound();
  }

  return (
    <div className="space-y-6">
      <div>
        <a href="/solutions" className="text-sm text-[#7F8C8D] hover:underline">
          ソリューション管理
        </a>
        {" > "}
        <a
          href={`/solutions/${solution.solution_id}`}
          className="text-sm text-[#7F8C8D] hover:underline"
        >
          {solution.name}
        </a>
        <h1 className="text-2xl font-bold text-[#2C3E50]">ソリューション編集</h1>
      </div>

      <SolutionEditForm solution={solution} />
    </div>
  );
}