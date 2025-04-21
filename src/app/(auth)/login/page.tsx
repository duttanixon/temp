"use client";

import '@/app/globals.css';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast, Toaster } from "sonner"; // sonnerから直接toastをインポート

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      // OAuth2トークンを取得するためのフォームデータを作成
      const formData = new URLSearchParams();
      formData.append('grant_type', 'password');
      formData.append('username', email); // usernameとしてemailを送信
      formData.append('password', password);
      formData.append('scope', '');
      formData.append('client_id', 'string');
      formData.append('client_secret', 'string');

      const loginUrl = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/auth/login`
      const loginResponse = await fetch(loginUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          "accept": "application/json",
        },
        body: formData.toString()
      });

      if (!loginResponse.ok) {
        console.log(email);
        console.log(password)

        const errorData = await loginResponse.json().catch(() => ({}));
        throw new Error(errorData.detail || "ログインに失敗しました");
      }

      // レスポンスからaccess_tokenを取得
      const loginData = await loginResponse.json();
      const accessToken = loginData.access_token; // access_tokenを取得
      console.log("取得したアクセストークン:", accessToken);

      // トークンを localStorage に保存
      localStorage.setItem('accessToken', accessToken);

      const myProfileUrl = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/users/me` 
      const myProfileResponse = await fetch(myProfileUrl, {
        headers: {
          'accept': 'application/json',
          'Authorization': `Bearer ${accessToken}`, // Bearerトークンを使用
        }
      });
      
      if (!myProfileResponse.ok) {
        throw new Error("ユーザー情報の取得に失敗しました");
      }

      const myProfile = await myProfileResponse.json();
      console.log("ユーザープロフィール:", myProfile);
      
      // 成功トーストを表示
      toast.success("ログイン成功", {
          description: "ダッシュボードにリダイレクトします",
      });

      // ダッシュボードなどにリダイレクト
      router.push("/");
      
    } catch (error) {
        console.error("ログインエラー:", error);
        // エラートーストを表示
        toast.error("ログイン失敗", {
            description: error instanceof Error ? error.message : "メールアドレスまたはパスワードが正しくありません",
        });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen w-full">
      {/* 左側のサイドバー */}
      <div className="w-full max-w-md p-8 text-white flex flex-col" style={{ backgroundColor: '#2c5d82' }}>
        <div className="flex items-center mb-8">
          <div className="h-20 w-20 rounded-full bg-white flex items-center justify-center">
            <span className="text-3xl font-bold" style={{ color: '#3498db' }}>EM</span>
          </div>
        </div>
        
        <h1 className="text-4xl font-bold mb-4">Edge Device Management System</h1>
        <p className="text-lg">
          Centralized control for all your IoT devices and AI solutions across multiple clients.
        </p>
        
        <div className="mt-auto">
          <p className="text-xs text-right mt-8">v1.0.0</p>
        </div>
      </div>

      {/* 右側のログインフォーム */}
      <div className="w-full flex items-center justify-center p-8" style={{ backgroundColor: '#f5f7f9' }}>
        <Card className="w-full max-w-md">
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl font-bold">Log in to your account</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <label htmlFor="email" className="text-sm font-medium">Email</label>
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label htmlFor="password" className="text-sm font-medium">Password</label>
                </div>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <div className="text-right">
                  <Link
                    href="/forgot-password"
                    className="text-sm text-blue-500 hover:text-blue-600" style={{ color: '#3498db' }}
                  >
                    Forgot password?
                  </Link>
                </div>
              </div>
              <Button type="submit" className="w-full" style={{ backgroundColor: '#3498db', color: 'white' }} disabled={isLoading}>
                {isLoading ? "ログイン中..." : "Log In"}
              </Button>
            </form>
            <div className="mt-4 text-center text-sm text-gray-500">
              Don't have an account? Contact your administrator.
            </div>
          </CardContent>
        </Card>
      </div>
        {/* Sonnerのトースターコンポーネントを追加 */}
        <Toaster richColors closeButton position="bottom-left" />
    </div>
  );
}