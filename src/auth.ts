import axios from "axios";
import NextAuth from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { z } from "zod";
import { authConfig } from "./auth.config";

// User型を定義
type User = {
    id: string;
    name: string;
    email: string;
    image?: string;
    role?: string;
    customerId?: string;
    accessToken?: string;
    lastLogin?: string;
    customerName?: string;
    firstName?: string;
    lastName?: string;
};

// ユーザー認証関数
async function getUser(email: string, password: string) {
    try {
        const loginUrl = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/auth/login`;

        // axiosを使用したリクエスト
        const formData = new URLSearchParams();
        formData.append("grant_type", "password");
        formData.append("username", email);
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

        const myProfileUrl = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/users/me`;

        // axiosでGETリクエスト（認証ヘッダー付き）
        const myProfileResponse = await axios.get(myProfileUrl, {
            headers: {
                accept: "application/json",
                Authorization: `Bearer ${accessToken}`,
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
                image: myProfile.image,
                // next-auth v5ではJWTに含める追加情報
                role: myProfile.role || "user",
                customerId: myProfile.customer_id,
                accessToken: accessToken,
                lastLogin: myProfile.last_login,
                customerName: myProfile.customer?.name,
                firstName: myProfile.first_name,
                lastName: myProfile.last_name,
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

// NextAuth v5の設定
export const { auth, signIn, signOut, handlers } = NextAuth({
    ...authConfig, // auth.configから設定を継承
    session: { strategy: "jwt" }, // JWT戦略を明示的に指定
    callbacks: {
        // JWT作成時のコールバック
        async jwt({ token, user }) {
            // 初回ログイン時にユーザー情報をトークンに追加
            if (user) {
                token.id = user.id;
                token.role = user.role;
                token.customerId = user.customerId;
                token.accessToken = user.accessToken;
                token.lastLogin = user.lastLogin;
                token.customerName = user.customerName;
                token.firstName = user.firstName;
                token.lastName = user.lastName;
            }
            return token;
        },
        // セッション作成時のコールバック
        async session({ session, token }) {
            // セッションにトークンの情報を追加
            if (token && session.user) {
                session.user.id = token.id as string;
                session.user.role = token.role as string;
                session.user.customerId = token.customerId as
                    | string
                    | undefined;
                session.accessToken = token.accessToken as string;
                session.user.lastLogin = token.lastLogin as string | undefined;
                session.user.customerName = token.customerName as
                    | string
                    | undefined;
                session.user.firstName = token.firstName;
                session.user.lastName = token.lastName;
            }
            return session;
        },
    },
    providers: [
        CredentialsProvider({
            // サインインフォームの設定（任意）
            name: "ログイン情報",
            credentials: {
                email: { label: "メールアドレス", type: "email" },
                password: { label: "パスワード", type: "password" },
            },
            async authorize(credentials) {
                // 認証ロジック
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
