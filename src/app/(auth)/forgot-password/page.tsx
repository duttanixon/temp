"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import Link from "next/link";
import { userService } from "@/services/userService";

const forgotPasswordSchema = z.object({
  email: z.string().email("有効なメールアドレスを入力してください"),
});

type ForgotPasswordFormValues = z.infer<typeof forgotPasswordSchema>;

export default function ForgotPasswordPage() {
  const router = useRouter();
  const [isSubmitted, setIsSubmitted] = useState(false);
  
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ForgotPasswordFormValues>({
    resolver: zodResolver(forgotPasswordSchema),
  });

  const onSubmit = async (data: ForgotPasswordFormValues) => {
    try {
      await userService.forgotPassword({ email: data.email });
      
      setIsSubmitted(true);
      toast.success("メールを送信しました", {
        description: "メールアドレスが登録されている場合、パスワードリセットリンクが送信されます。",
      });
    } catch (error) {
      const errorMessage = error instanceof Error 
        ? error.message 
        : "エラーが発生しました";
        
      toast.error("エラーが発生しました", {
        description: errorMessage,
      });
    }
  };

  if (isSubmitted) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Card className="w-full max-w-md">
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl font-bold text-[#2C3E50] text-center">
              メールを確認してください
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-gray-600 text-center">
              メールアドレスが登録されている場合、パスワードリセットリンクをお送りしました。
              メールボックスをご確認ください。
            </p>
            <p className="text-sm text-gray-600 text-center">
              メールが届かない場合は、迷惑メールフォルダもご確認ください。
            </p>
            <div className="pt-4">
              <Link href="/login">
                <Button 
                  className="w-full"
                  variant="outline"
                >
                  ログインページに戻る
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold text-[#2C3E50]">
            パスワードをリセット
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="email" className="text-sm text-gray-700">
                登録されているメールアドレスを入力してください
              </label>
              <Input
                id="email"
                type="email"
                {...register("email")}
                placeholder="email@example.com"
                className="text-[#2C3E50]"
              />
              {errors.email && (
                <p className="text-sm text-red-500">{errors.email.message}</p>
              )}
            </div>
            
            <Button
              type="submit"
              className="w-full"
              style={{ backgroundColor: "#3498db", color: "white" }}
              disabled={isSubmitting}
            >
              {isSubmitting ? "送信中..." : "リセットリンクを送信"}
            </Button>
          </form>
          
          <div className="mt-4 text-center">
            <Link
              href="/login"
              className="text-sm text-blue-500 hover:text-blue-600"
              style={{ color: "#3498db" }}
            >
              ログインページに戻る
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}