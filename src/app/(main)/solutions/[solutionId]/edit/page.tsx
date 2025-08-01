// src/app/(main)/solutions/[solutionId]/edit/page.tsx
import { auth } from "@/auth";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
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
        <Breadcrumb className="text-sm text-[#7F8C8D]">
          <BreadcrumbList>
            <BreadcrumbItem className="hover:underline">
              <BreadcrumbLink href="/solutions">ソリューション</BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator className="text-[#7F8C8D]" />
            <BreadcrumbItem className="hover:underline">
              <BreadcrumbLink href={`/solutions/${solutionId}/details`}>
                {solution.name} - 詳細情報
              </BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator className="text-[#7F8C8D]" />
            <BreadcrumbItem>編集</BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
        <h1 className="text-2xl font-bold text-[#2C3E50]">
          {solution.name} - 編集
        </h1>
      </div>
      <SolutionEditForm solution={solution} />
    </div>
  );
}
