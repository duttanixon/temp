export default async function page() {
    // // サーバーサイドでセッションを取得
    // const session = await getServerSession(authOptions);
    // // ADMINではない場合は404ページにリダイレクト
    // if (session?.user?.role !== "ADMIN") {
    //     return (
    //         <div className="flex flex-col p-8">
    //             <h1 className="text-3xl font-bold underline">404 Not Found</h1>
    //         </div>
    //     );
    // }

    return (
        <div className="flex flex-col p-8">
            <h1 className="text-3xl font-bold underline">Users</h1>
        </div>
    );
}
