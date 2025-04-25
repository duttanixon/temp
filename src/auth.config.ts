import type { NextAuthConfig } from 'next-auth';

export const authConfig = {
    pages: {
        signIn: '/login',
        // signOut: '/logout',
        // error: '/error',
        // verifyRequest: '/verify-request',
    },
    callbacks: {
        authorized({
            auth,
            request: {nextUrl}
        }) {
            const isLoggedIn = !!auth?.user;    // ログインしているかどうか
            const isOnDashboard = nextUrl.pathname.startsWith('/dashboard'); // ダッシュボードにいるかどうか
            if (isOnDashboard) {
                if (!isLoggedIn) return true;
                return false;   // ログインしていなければloginページにリダイレクト
            } else if (isLoggedIn && nextUrl.pathname === '/login') {
                return Response.redirect(new URL('/dashboard', nextUrl));
            }
            return true;
        }
    },
    providers: [],  // ログインオプション auth/index.ts側で設定
} satisfies NextAuthConfig
