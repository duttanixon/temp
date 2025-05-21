// app/(main)/analytics/cityeye/page.tsx
import { auth } from "@/auth";
import CityEyeClient from "./_components/CityEyeClient";
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "City Eye Analytics Dashboard",
  description: "Urban behavior and traffic analysis dashboard",
};

export default async function CityEyePage() {
  // Get the session to verify authentication
  const session = await auth();
  
  // You could fetch initial data here if needed
  // const initialData = await fetchInitialData(accessToken);
  return (
    <div >
      <CityEyeClient />
    </div>
  );
}