import NextAuth, { NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";

// NextAuth オプションを設定
export const authOptions: NextAuthOptions = {
    providers: [
        CredentialsProvider({
            // 表示名
            name: "ログイン情報",
            // プロバイダー固有の設定
            credentials: {
                email: { label: "メールアドレス", type: "email" },
                password: { label: "パスワード", type: "password" },
            },
            // 認証関数
            async authorize(credentials) {
                if (!credentials?.email || !credentials?.password) {
                    return null;
                }

                try {
                    // OAuth2トークンを取得するためのフォームデータを作成
                    const formData = new URLSearchParams();
                    formData.append("grant_type", "password");
                    formData.append("username", credentials.email);
                    formData.append("password", credentials.password);
                    formData.append("scope", "");
                    formData.append("client_id", "string");
                    formData.append("client_secret", "string");

                    // APIエンドポイント
                    const loginUrl = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/auth/login`;

                    // ログインリクエスト
                    const loginResponse = await fetch(loginUrl, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/x-www-form-urlencoded",
                            Accept: "application/json",
                        },
                        body: formData.toString(),
                    });

                    if (!loginResponse.ok) {
                        console.error(
                            "ログイン失敗:",
                            await loginResponse.text()
                        );
                        return null;
                    }

                    // レスポンスからaccess_tokenを取得
                    const loginData = await loginResponse.json();
                    const accessToken = loginData.access_token;

                    if (!accessToken) {
                        console.error("アクセストークンが見つかりません");
                        return null;
                    }

                    // ユーザー情報を取得
                    const myProfileUrl = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/users/me`;
                    const myProfileResponse = await fetch(myProfileUrl, {
                        headers: {
                            Accept: "application/json",
                            Authorization: `Bearer ${accessToken}`,
                        },
                    });

                    if (!myProfileResponse.ok) {
                        console.error(
                            "ユーザー情報取得失敗:",
                            await myProfileResponse.text()
                        );
                        return null;
                    }

                    // カスタマー情報を取得
                    const userProfile = await myProfileResponse.json();
                    let customerName = "";

                    if (userProfile.customer_id) {
                        const customerUrl = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/customers/${userProfile.customer_id}`;
                        const customerResponse = await fetch(customerUrl, {
                            headers: {
                                Accept: "application/json",
                                Authorization: `Bearer ${accessToken}`,
                            },
                        });

                        if (!customerResponse.ok) {
                            console.error(
                                "カスタマー情報取得失敗:",
                                await customerResponse.text()
                            );
                            // return null;
                        } else {
                            const customerData = await customerResponse.json();
                            customerName = customerData.name || "";
                            console.log("カスタマーデータ:", customerData);
                        }
                    }
                    console.log("ユーザープロフィール:", userProfile);

                    // next-auth用のユーザーオブジェクトを返す
                    return {
                        id: userProfile.user_id,
                        email: userProfile.email,
                        name: `${userProfile.first_name || ""} ${
                            userProfile.last_name || ""
                        }`.trim(),
                        role: userProfile.role,
                        customerId: userProfile.customer_id,
                        accessToken: accessToken, // トークンも保存
                        lastLogin: userProfile.last_login,
                        customerName: customerName,
                    };
                } catch (error) {
                    console.error("認証エラー:", error);
                    return null;
                }
            },
        }),
    ],
    // セッション設定
    session: {
        strategy: "jwt",
        maxAge: 60 * 60 * 8, // 8時間
    },
    // JWT設定
    jwt: {
        maxAge: 60 * 60 * 8, // 8時間
    },
    // コールバック
    callbacks: {
        async jwt({ token, user }) {
            // 初回ログイン時にユーザー情報をトークンに追加
            if (user) {
                token.id = user.id;
                token.role = user.role;
                token.customerId = user.customerId;
                token.accessToken = user.accessToken;
                token.lastLogin = user.lastLogin;
                token.customerName = user.customerName;
            }
            return token;
        },
        async session({ session, token }) {
            // セッションにユーザー情報を追加
            if (token) {
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
            }
            return session;
        },
    },
    // カスタムページ
    pages: {
        signIn: "/login",
        error: "/login", // エラー時もログインページに
    },
    // デバッグモード（本番環境ではfalseに）
    debug: process.env.NODE_ENV === "development",
};

// API Route handler
const handler = NextAuth(authOptions);
export { handler as GET, handler as POST };
