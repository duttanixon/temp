import axios from "axios";
import NextAuth from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { z } from "zod";
import { authConfig } from "./auth.config";
import { JWT } from "next-auth/jwt";

// ユーザー認証関数
async function getUser(email: string, password: string) {
  console.log("🔑 AUTH: Authenticating user:", email);
  try {
    const loginUrl = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/auth/login`;
    console.log("🔑 AUTH: Sending request to:", loginUrl);

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

    console.log("🔑 AUTH: Login successful, received token");
    // レスポンスからaccess_tokenを取得
    const accessToken = loginResponse.data.access_token;

    const myProfileUrl = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/users/me`;
    console.log("🔑 AUTH: Fetching user profile from:", myProfileUrl);

    // axiosでGETリクエスト（認証ヘッダー付き）
    const myProfileResponse = await axios.get(myProfileUrl, {
      headers: {
        accept: "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
    });

    const myProfile = myProfileResponse.data;
    console.log("🔑 AUTH: Retrieved user profile, role:", myProfile.role);

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
    console.error("🔑 AUTH: Authentication error:", error);
    throw error;
  }
}

// NextAuth v5の設定
export const { auth, signIn, signOut, handlers } = NextAuth({
  ...authConfig, // auth.configから設定を継承
  session: { strategy: "jwt" }, // JWT戦略を明示的に指定

  callbacks: {
    // JWT作成時のコールバック
    // JWT run during inital login, on every api request and during session updates update() from client via useSession()
    async jwt({ token, user }: { token: JWT; user?: any }) {
      console.log(
        "🔐 AUTH JWT Callback:",
        user ? "Initial login with user data" : "Updating existing token"
      );

      // If token already has an error, don't try to refresh it again
      if (token.error) {
        console.log(
          "🔐 AUTH JWT: Token has error, not refreshing:",
          token.error
        );
        return null;
      }
      // 初回ログイン時にユーザー情報をトークンに追加
      if (user) {
        console.log("🔐 AUTH JWT: Creating new token for user:", user.email);
        const expirationMinutes =
          Number(process.env.TOKEN_EXPIRATION_TIME) || 30; // Get the number of minutes (e.g., 30)

        token = {
          ...token,
          ...user,
          tokenExpires: Date.now() + expirationMinutes * 60 * 1000,
        };
        console.log(
          "🔐 AUTH JWT: Token created, expires in:",
          expirationMinutes,
          "minutes"
        );
        return token;
      }

      // For existing token, check if it is expired
      if (token.tokenExpires && typeof token.tokenExpires === "number") {
        const timeToExpiration = token.tokenExpires - Date.now();
        console.log(
          "🔐 AUTH JWT: Existing token expires in:",
          Math.round(timeToExpiration / 1000 / 60),
          "minutes"
        );

        const checkTimeMinutes =
          Number(process.env.TOKEN_EXPIRATION_CHECK_TIME) || 5; // Get the number of minutes (e.g., 1)
        if (Date.now() > token.tokenExpires - checkTimeMinutes * 60 * 1000) {
          console.log(
            "🔐 AUTH JWT: Token needs refresh, attempting refresh..."
          );
          try {
            // Try to refresh the token using backend
            const refreshUrl = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/auth/refresh-token`;
            const response = await fetch(refreshUrl, {
              method: "POST",
              headers: {
                Authorization: `Bearer ${token.accessToken}`,
                "Content-Type": "application/json",
              },
            });
            // If refresh succeeds, update token
            if (response.ok) {
              console.log("🔐 AUTH JWT: Token refresh successful");
              const data = await response.json();
              const expirationMinutes =
                Number(process.env.TOKEN_EXPIRATION_TIME) || 30;
              return {
                ...token,
                accessToken: data.access_token,
                tokenExpires: Date.now() + expirationMinutes * 60 * 1000,
              };
            } else {
              // If refresh fails, token is invalid - force re-login
              console.log(
                "🔐 AUTH JWT: Token refresh failed, session expired",
                await response.text()
              );
              return { ...token, error: "RefreshAccessTokenError" };
            }
          } catch (error) {
            console.error("🔐 AUTH JWT: Error refreshing access token:", error);
            return { ...token, error: "RefreshAccessTokenError" };
          }
        }
      }
      return token;
    },
    // セッション作成時のコールバック
    async session({ session, token }) {
      console.log("🔓 AUTH SESSION Callback: Creating session from token");
      // Return a new session object with all the required properties
      // If there was an error refreshing the token, trigger a session error
      // called after jwt callback and upon useSession() in client
      if (token.error) {
        console.log("🔓 AUTH SESSION: Token has error:", token.error);
        session.error = token.error;
      }

      console.log("🔓 AUTH SESSION: Session created for user:", token.email);
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
        console.log("🔑 AUTH Provider: Authorizing credentials");
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
            console.log(
              "🔑 AUTH Provider: Credentials valid, attempting authentication"
            );
            const user = await getUser(email, password);
            console.log("🔑 AUTH Provider: Authentication successful");
            return user;
          } catch (error) {
            console.error("🔑 AUTH Provider: Authentication error:", error);
            return null;
          }
        }
        console.log("🔑 AUTH Provider: Invalid credentials format");
        return null;
      },
    }),
  ],
});
