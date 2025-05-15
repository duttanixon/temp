import { auth } from "@/auth";
import { notFound } from "next/navigation";
import SolutionActions from "../_components/SolutionActions";
import SolutionInfoCard from "./_components/SolutionDetailsTabs";

async function getSolution(solutionId: string, accessToken: string) {
  const apiUrl = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/solutions/${solutionId}`;

  try {
    const response = await fetch(apiUrl, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
      cache: "no-store",
    });

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

export default async function SolutionDetailsPage({ params }: Props) {
  const resolvedParams = await params;
  const session = await auth();
  const accessToken = session?.accessToken ?? "";
  const solutionId = resolvedParams.solutionId;
  const isAdmin = session?.user?.role === "ADMIN";

  const solution = await getSolution(solutionId, accessToken);

  if (!solution) {
    notFound();
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <a href="/solutions" className="text-sm text-[#7F8C8D] hover:underline">
            ソリューション管理
          </a>
          <h1 className="text-2xl font-bold text-[#2C3E50]">{solution.name}</h1>
        </div>
        {isAdmin && <SolutionActions solution={solution} />}
      </div>

      <SolutionInfoCard solution={solution} />
    </div>
  );
}