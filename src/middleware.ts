// 古いimport文を削除
// import { withAuth } from "next-auth/middleware";
import { auth } from "@/auth"; // auth.tsからauthをインポート
import { NextResponse } from "next/server";

// 新しいミドルウェア関数
export default auth(async function middleware(req) {
    const token = req.auth; // req.nextauth.tokenではなくreq.authを使用
    const path = req.nextUrl.pathname;

    // ログイン済みでログインページにアクセスしようとした場合
    if (token && path === "/login") {
        // ダッシュボードにリダイレクト
        return NextResponse.redirect(
            new URL(process.env.NEXT_PUBLIC_AUTH_REDIRECT_URL || "/", req.url)
        );
    }

    // それ以外は通常の処理を続行
    return NextResponse.next();
});

// ミドルウェアの設定
export const config = {
    matcher: [
        "/login", // ログインページも処理対象に含める
        "/((?!api|_next/static|_next/image|favicon.ico|public|api/auth).*)",
    ],
};
