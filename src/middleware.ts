import { withAuth } from "next-auth/middleware";
import { NextResponse } from "next/server";

// 認証済みか確認するミドルウェア
export default withAuth(
    function middleware(req) {
        const token = req.nextauth.token;
        const path = req.nextUrl.pathname;

        // ログイン済みでログインページにアクセスしようとした場合
        if (token && path === "/login") {
            // ダッシュボードにリダイレクト
            return NextResponse.redirect(
                new URL(
                    process.env.NEXT_PUBLIC_AUTH_REDIRECT_URL || "/",
                    req.url
                )
            );
        }

        // それ以外は通常の処理を続行
        return NextResponse.next();
    },
    {
        callbacks: {
            // すべてのリクエストでミドルウェアを実行するためにtrueを返す
            authorized: ({ token, req }) => {
                const path = req.nextUrl.pathname;

                // ログインページの場合は認証チェックをバイパス
                if (path === "/login") {
                    return true;
                }

                // それ以外のルートでは通常の認証チェック
                return !!token;
            },
        },
        // 認証されていない場合のリダイレクト先
        pages: {
            signIn: "/login",
        },
    }
);

// どのパスを保護するか定義（ログインページも含める）
export const config = {
    matcher: [
        "/login", // ログインページも処理対象に含める
        "/((?!api|_next/static|_next/image|favicon.ico|public|api/auth).*)",
    ],
};
