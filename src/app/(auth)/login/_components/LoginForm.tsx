"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { signIn } from "next-auth/react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

export function LoginForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

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

      // Add redirect to dashboard
      // router.push("/users");
      window.location.href = "/users";
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
    <Card className="w-full max-w-md">
      <CardHeader className="space-y-1">
        <CardTitle className="text-2xl font-bold text-[#2C3E50]">
          ログイン
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4 text-[#7C8C8D]">
          <div className="space-y-2">
            <label htmlFor="email" className="text-sm">
              メールアドレス
            </label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="text-[#2C3E50]"
              required
            />
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label htmlFor="password" className="text-sm">
                パスワード
              </label>
            </div>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="text-[#2C3E50]"
              required
            />
            <div className="text-right">
              <Link
                href="/reset-password"
                className="text-sm text-blue-500 hover:text-blue-600"
                style={{ color: "#3498db" }}
              >
                パスワードをお忘れですか？
              </Link>
            </div>
          </div>
          <Button
            type="submit"
            className="w-full cursor-pointer"
            style={{ backgroundColor: "#3498db", color: "white" }}
            disabled={isLoading}
          >
            {isLoading ? "ログイン中..." : "ログイン"}
          </Button>
        </form>
        <div className="mt-4 text-center text-sm text-[#7C8C8D]">
          <p>{"アカウントをお持ちではありませんか？"}</p>
          <p>{"管理者にお問い合わせください。"}</p>
        </div>
      </CardContent>
    </Card>
  );
}
