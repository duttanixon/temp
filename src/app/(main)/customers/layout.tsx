import { authOptions } from "@/app/api/auth/[...nextauth]/route";
import { getServerSession } from "next-auth";
import Forbidden from "../_components/Forbidden";

export default async function MainLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    // サーバーサイドでセッションを取得
    const session = await getServerSession(authOptions);
    // ADMINではない場合はforbiddenページにリダイレクト
    if (session?.user?.role !== "ADMIN") {
        return <Forbidden />;
    }

    return <>{children}</>;
}
