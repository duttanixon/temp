"use client";

import { signIn, signOut, useSession } from "next-auth/react";
import { useRouter } from "next/navigation";

// 認証用カスタムフック
export function useAuth() {
    const { data: session, status } = useSession();
    const router = useRouter();

    // ログイン処理
    const login = async (email: string, password: string) => {
        try {
            const result = await signIn("credentials", {
                email,
                password,
                redirect: false,
            });

            if (result?.error) {
                return { success: false, error: result.error };
            }

            return { success: true };
        } catch (error) {
            console.error("ログインエラー:", error);
            return { success: false, error: "認証に失敗しました" };
        }
    };

    // ログアウト処理
    const logout = async () => {
        await signOut({ redirect: false });
        router.push("/login");
    };

    // 認証状態
    const isAuthenticated = status === "authenticated";

    // ユーザーのロール
    const userRole = session?.user?.role;

    // アクセストークン
    const accessToken = session?.accessToken;

    return {
        session,
        status,
        login,
        logout,
        isAuthenticated,
        userRole,
        accessToken,
    };
}
