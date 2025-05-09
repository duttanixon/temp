"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { signIn } from "next-auth/react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { toast } from "sonner";

export function LoginForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();
  const searchParams = useSearchParams();
  const [callbackUrl, setCallbackUrl] = useState("");

  // callbackUrlを取得
  useEffect(() => {
    // searchParamsからcallbackUrlを取得し、デコード
    const callback = searchParams.get("callbackUrl");
    if (callback) {
      setCallbackUrl(decodeURIComponent(callback));
    }
  }, [searchParams]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    console.log("📝 LOGIN: Form submitted with email:", email);

    try {
      // Use next-auth's signIn directly
      console.log("📝 LOGIN: Calling signIn() with credentials");
      const result = await signIn("credentials", {
        email,
        password,
        redirect: false,
      });

      console.log("📝 LOGIN: SignIn result:", result);

      if (result?.error) {
        throw new Error(result.error || "ログインに失敗しました");
      }

      // 成功トーストを表示
      console.log("📝 LOGIN: Login successful, redirecting");
      toast.success("ログイン成功", {
        description: "ダッシュボードにリダイレクトします",
      });

      // リダイレクト先を決定（callbackUrl がある場合はそちらを優先）
      const redirectUrl = callbackUrl || "/";
      window.location.href = redirectUrl;
    } catch (error) {
      console.error("📝 LOGIN: Login error:", error);
      // エラートーストを表示
      toast.error("ログイン失敗", {
        description:
          error instanceof Error
            ? error.message
            : "メールアドレスまたはパスワードが正しくありません",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-md border-2">
      <CardHeader className="space-y-1">
        <CardTitle className="text-2xl font-bold">
          Log in to your account
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label htmlFor="email" className="text-sm font-medium">
              Email
            </label>
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
              <label htmlFor="password" className="text-sm font-medium">
                Password
              </label>
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
                className="text-sm text-blue-500 hover:text-blue-600">
                パスワードをお忘れですか？
              </Link>
            </div>
          </div>
          <div className="flex justify-center">
            <Button
              type="submit"
              className="w-35 rounded-full cursor-pointer bg-[#2b96cc] hover:bg-[#2483b3] text-white"
              disabled={isLoading}>
              {isLoading ? "ログイン中..." : "ログイン"}
            </Button>
          </div>
        </form>
        <div className="mt-4 text-center text-sm text-gray-500">
          {"Don't have an account? Contact your administrator."}
        </div>
      </CardContent>
    </Card>
  );
}
