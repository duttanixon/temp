import axios from "axios";
import NextAuth from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { z } from "zod";
import { authConfig } from "./auth.config";
import { JWT } from "next-auth/jwt";

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

    const myProfileUrl = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/users/me`;

    // axiosでGETリクエスト（認証ヘッダー付き）
    const myProfileResponse = await axios.get(myProfileUrl, {
      headers: {
        accept: "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
    });

    const myProfile = myProfileResponse.data;

    return {
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
    };
  } catch (error) {
    console.error("Authentication error:", error);
    throw error;
  }
}

// NextAuth v5の設定
export const { auth, signIn, signOut, handlers } = NextAuth({
  ...authConfig, // auth.configから設定を継承
  session: { strategy: "jwt" }, // JWT戦略を明示的に指定

  callbacks: {
    // JWT作成時のコールバック
    async jwt({ token, user }: { token: JWT; user?: any }) {
      // 初回ログイン時にユーザー情報をトークンに追加
      if (user) {
        token = {
          ...token,
          ...user,
          tokenExpires: Date.now() + 30 * 60 * 1000,
        };

        return token;
      }

      // For existing token, check if it is exppired
      if (token.tokenExpires && typeof token.tokenExpires === "number") {
        // If token is expired
        if (Date.now() > token.tokenExpires) {
          try {
            // Try to refresh the token using backend
            const refreshUrl = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/auth/refresh-token`;
            const response = await fetch(refreshUrl, {
              headers: {
                Authorization: `Bearer ${token.accessToken}`,
                "Content-Type": "application/json",
              },
            });
            // If refresh succeeds, update token
            if (response.ok) {
              const userData = await response.json();
              return {
                ...token,
                accessToken: token.accessToken, // Keep the same token for now
                tokenExpires: Date.now() + 30 * 60 * 1000, // Extend by 30 min
              };
            } else {
              // If refresh fails, token is invalid - force re-login
              console.log("Token refresh failed, session expired");
              return { ...token, error: "RefreshAccessTokenError" };
            }
          } catch (error) {
            console.error("Error refreshing access token:", error);
            return { ...token, error: "RefreshAccessTokenError" };
          }
        }
      }
      return token;
    },
    // セッション作成時のコールバック
    async session({ session, token }) {
      // Return a new session object with all the required properties
      // If there was an error refreshing the token, trigger a session error
      if (token.error) {
        session.error = token.error;
      }

      // Pass token data to the session
      return {
        ...session,
        error: token.error,
        user: {
          ...session.user,
          id: token.id as string,
          email: token.email as string,
          name: token.name as string,
          image: token.image as string | undefined,
          role: token.role as string,
          customerId: token.customerId as string | undefined,
          lastLogin: token.lastLogin as string | undefined,
          customerName: token.customerName as string | undefined,
          firstName: token.firstName as string | undefined,
          lastName: token.lastName as string | undefined,
        },
        accessToken: token.accessToken as string,
        tokenExpires: token.tokenExpires as number,
      };
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
            return await getUser(email, password);
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
