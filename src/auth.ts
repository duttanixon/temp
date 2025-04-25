import NextAuth from 'next-auth';
import Credentials from 'next-auth/providers/credentials';
import { z } from 'zod';
import { authConfig } from './auth.config';

// User型を定義
type User = {
    id: string;
    name: string;
    email: string;
    image?: string;
  };

async function getUser(email: string, password: string) {
    const loginUrl = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/auth/login`;
    const formData = new URLSearchParams();
    formData.append('grant_type', 'password');
    formData.append('username', email); // usernameとしてemailを送信
    formData.append('password', password);
    formData.append('scope', '');
    formData.append('client_id', 'string');
    formData.append('client_secret', 'string');
    const loginResponse = await fetch(loginUrl, {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "accept": "application/json",
        },
        body: formData.toString()
    });
    if (!loginResponse.ok) {
        const errorData = await loginResponse.json().catch(() => ({}));
        throw new Error(errorData.detail || "ログインに失敗しました");
    }
    // レスポンスからaccess_tokenを取得
    const loginData = await loginResponse.json();
    const accessToken = loginData.access_token; // access_tokenを取得
    console.log("取得したアクセストークン:", accessToken);
    // トークンを localStorage に保存
    localStorage.setItem('accessToken', accessToken);
    const myProfileUrl = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/users/me`;
    const myProfileResponse = await fetch(myProfileUrl, {
        headers: {
            'accept': 'application/json',
        }
    });
    if (!myProfileResponse.ok) {
        throw new Error("ユーザー情報の取得に失敗しました");
    }
    const myProfile = await myProfileResponse.json();
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
}

export const { auth, signIn, signOut, handlers } = NextAuth({
    ...authConfig,
    providers: [Credentials({
        async authorize(credentials): Promise<User | null> {
            const parsedCredentials = z
                .object({
                    email: z.string().email(),
                    password: z.string().min(6),
                })
                .safeParse(credentials);

            if (parsedCredentials.success) {
                const { email, password } = parsedCredentials.data;
                const userData = await getUser(email, password);
                if (!userData) return null;
                return userData.user;
            }

            return null;
        }
    })],
});