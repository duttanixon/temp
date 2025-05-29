import UserEditForm from "@/app/(main)/users/[id]/edit/_components/UserEditForm";
import { auth } from "@/auth";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";

async function getUser(userId: string, accessToken: string) {
  const apiUrl = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/users/${userId}`;

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
  params: Promise<{
    id: string;
  }>;
};
export default async function UserEditPage({ params }: Props) {
  const resolvedParams = await params;
  // サーバーサイドでセッションを取得
  const session = await auth();
  const role = session?.user?.role;
  const accessToken = session?.accessToken ?? "";
  const userId = resolvedParams.id;
  const user = await getUser(userId, accessToken);
  console.log("accessToken:", accessToken);
  console.log("typeof accessToken:", typeof accessToken);
  console.log("accessToken keys:", Object.keys(accessToken));
  console.log("session:", session);
  console.log("user:", user);

  console.log(" ADD USER PAGE: Session data:", session);
  if (role !== "ADMIN" && role !== "CUSTOMER_ADMIN") {
    return <div className="text-red-500">権限がありません</div>;
  }

  return (
    <div className="flex flex-col">
      <Breadcrumb className="text-sm text-[#7F8C8D]">
        <BreadcrumbList>
          <BreadcrumbItem className=" hover:underline">
            <BreadcrumbLink href="/users">ユーザー</BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator className="text-[#7F8C8D]" />
          <BreadcrumbItem>{`${user.last_name} ${user.first_name}`}</BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
      <UserEditForm
        accessToken={accessToken}
        role={role}
        userId={userId}
        user={user}
      />
    </div>
  );
}
