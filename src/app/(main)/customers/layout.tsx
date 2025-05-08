import { auth } from "@/auth";
import Forbidden from "@/app/(main)/_components/Forbidden";

export default async function MainLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // サーバーサイドでセッションを取得
  const session = await auth();
  // ADMINではない場合はforbiddenページにリダイレクト
  if (session?.user?.role !== "ADMIN") {
    return <Forbidden />;
  }

  return <>{children}</>;
}
