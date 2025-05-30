import { auth } from "@/auth";
import { redirect } from "next/navigation";
import SolutionCreateForm from "../_components/SolutionCreateForm";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";

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
        <Breadcrumb className="text-sm text-[#7F8C8D]">
          <BreadcrumbList>
            <BreadcrumbItem className=" hover:underline">
              <BreadcrumbLink href="/solutions">ソリューション</BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator className="text-[#7F8C8D]" />
            <BreadcrumbItem>ソリューションの作成</BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
        <h1 className="text-2xl font-bold text-[#2C3E50]">
          ソリューションの作成
        </h1>
      </div>

      <SolutionCreateForm />
    </div>
  );
}
