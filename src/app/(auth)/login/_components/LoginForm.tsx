"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/hooks/useAuth";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

export function LoginForm() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const router = useRouter();
    const { login } = useAuth(); // Next Authのカスタムフックを使用

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);

        try {
            // next-authを使用してログイン
            const result = await login(email, password);

            if (!result.success) {
                throw new Error(result.error || "ログインに失敗しました");
            }

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
                            <label
                                htmlFor="password"
                                className="text-sm font-medium">
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
                                className="text-sm text-blue-500 hover:text-blue-600"
                                style={{ color: "#3498db" }}>
                                Forgot password?
                            </Link>
                        </div>
                    </div>
                    <Button
                        type="submit"
                        className="w-full cursor-pointer"
                        style={{ backgroundColor: "#3498db", color: "white" }}
                        disabled={isLoading}>
                        {isLoading ? "ログイン中..." : "Log In"}
                    </Button>
                </form>
                <div className="mt-4 text-center text-sm text-gray-500">
                    {"Don't have an account? Contact your administrator."}
                </div>
            </CardContent>
        </Card>
    );
}
