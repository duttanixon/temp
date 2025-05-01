import axios from "axios"; // axiosをインポート
import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";
import { z } from "zod";
import { authConfig } from "./auth.config";

// User型を定義
type User = {
    id: string;
    name: string;
    email: string;
    image?: string;
};

async function getUser(email: string, password: string) {
    try {
        const loginUrl = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/auth/login`;

        // axiosを使用したリクエスト
        const formData = new URLSearchParams();
        formData.append("grant_type", "password");
        formData.append("username", email); // usernameとしてemailを送信
        formData.append("password", password);
        formData.append("scope", "");
        formData.append("client_id", "string");
        formData.append("client_secret", "string");

        // axiosでPOSTリクエスト
        const loginResponse = await axios.post(loginUrl, formData.toString(), {
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
                accept: "application/json",
            },
        });

        // レスポンスからaccess_tokenを取得
        const accessToken = loginResponse.data.access_token;
        console.log("取得したアクセストークン:", accessToken);

        // // トークンを localStorage に保存
        // // 注意: Next.jsのサーバーコンポーネントではlocalStorageは使用できません
        // // クライアントサイドでのみ実行されるようにする必要があります
        // if (typeof window !== "undefined") {
        //     localStorage.setItem("accessToken", accessToken);
        // }

        const myProfileUrl = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/users/me`;

        // axiosでGETリクエスト（認証ヘッダー付き）
        const myProfileResponse = await axios.get(myProfileUrl, {
            headers: {
                accept: "application/json",
                Authorization: `Bearer ${accessToken}`, // 認証トークンをヘッダーに追加
            },
        });

        const myProfile = myProfileResponse.data;
        console.log("ユーザープロフィール:", myProfile);

        return {
            accessToken,
            user: {
                id: myProfile.id,
                name: myProfile.name,
                email: myProfile.email,
                image: myProfile.image, // 画像URL
                // 追加のユーザープロフィール情報があればここに追加
            },
        };
    } catch (error) {
        // axiosのエラーハンドリング
        if (axios.isAxiosError(error)) {
            const errorMessage =
                error.response?.data?.detail || "ログインに失敗しました";
            throw new Error(errorMessage);
        }
        throw error;
    }
}

export const { auth, signIn, signOut, handlers } = NextAuth({
    ...authConfig,
    providers: [
        Credentials({
            async authorize(credentials): Promise<User | null> {
                const parsedCredentials = z
                    .object({
                        email: z.string().email(),
                        password: z.string().min(6),
                    })
                    .safeParse(credentials);

                if (parsedCredentials.success) {
                    const { email, password } = parsedCredentials.data;
                    try {
                        const userData = await getUser(email, password);
                        if (!userData) return null;
                        return userData.user;
                    } catch (error) {
                        console.error("認証エラー:", error);
                        return null;
                    }
                }

                return null;
            },
        }),
    ],
});
