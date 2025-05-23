// app/(main)/analytics/cityeye/page.tsx
import { auth } from "@/auth";
import CityEyeClient from "../_components/CityEyeClient";
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "City Eye Analytics Dashboard",
  description: "Urban behavior and traffic analysis dashboard",
};

// Define props for the page, including params from the dynamic route
type CityEyeDynamicPageProps = {
  params: Promise<{ solutionId: string }>;
};

export default async function CityEyePage({ params }: CityEyeDynamicPageProps) {
  // Get the session to verify authentication
  const resolvedParams = await params;
  const solutionId = resolvedParams.solutionId;
  const session = await auth();

  // You could fetch initial data here if needed
  // const initialData = await fetchInitialData(accessToken);
  return (
    <div>
      <CityEyeClient solutionId={solutionId} />
    </div>
  );
}
