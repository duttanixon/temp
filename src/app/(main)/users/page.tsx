import { authOptions } from "@/app/api/auth/[...nextauth]/route";
import { getServerSession } from "next-auth";

export default async function page() {
    // サーバーサイドでセッションを取得
    const session = await getServerSession(authOptions);
    console.log(session);
    return (
        <div className="flex flex-col">
            <h1 className="text-3xl font-bold underline">Users</h1>
        </div>
    );
}
