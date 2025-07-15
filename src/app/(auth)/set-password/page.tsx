"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { FormField } from "@/components/forms/FormField";
import { toast } from "sonner";
import { userService } from "@/services/userService";
import { passwordSetSchema, PasswordSetFormValues } from "@/schemas/userSchemas";

export default function SetPasswordPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const [isValidToken, setIsValidToken] = useState(false);
  const [userInfo, setUserInfo] = useState({ email: "", name: "" });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) {
      toast.error("無効なリンクです");
      router.push("/login");
      return;
    }

    userService.verifyResetToken(token)
      .then((response) => {
        if (response.valid) {
          setIsValidToken(true);
          setUserInfo({ email: response.email, name: response.name });
        } else {
          toast.error("無効または期限切れのリンクです");
          router.push("/login");
        }
      })
      .catch(() => {
        toast.error("エラーが発生しました");
        router.push("/login");
      })
      .finally(() => setLoading(false));
  }, [token, router]);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<PasswordSetFormValues>({
    resolver: zodResolver(passwordSetSchema),
  });

  const onSubmit = async (data: PasswordSetFormValues) => {
    try {
      await userService.setPassword(token!, data.password);
      toast.success("パスワードが設定されました");
      router.push("/login");
    } catch (error) {
      toast.error("パスワードの設定に失敗しました");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-gray-600">読み込み中...</div>
      </div>
    );
  }

  if (!isValidToken) {
    return null;
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow">
        <div>
          <h2 className="text-2xl font-bold text-center text-[#2C3E50]">パスワードの設定</h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            {userInfo.name} ({userInfo.email})
          </p>
        </div>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <FormField
            id="password"
            label="新しいパスワード"
            type="password"
            register={register}
            errors={errors}
            required
            as="input"
            inputClassName="w-full h-10 px-3 border border-[#BDC3C7] rounded-md"
          />
          <FormField
            id="verify_password"
            label="パスワード（確認用）"
            type="password"
            register={register}
            errors={errors}
            required
            as="input"
            inputClassName="w-full h-10 px-3 border border-[#BDC3C7] rounded-md"
          />
          <Button
            type="submit"
            className="w-full bg-[#27AE60] text-white hover:bg-[#219653] h-10"
            disabled={isSubmitting}
          >
            {isSubmitting ? "設定中..." : "パスワードを設定"}
          </Button>
        </form>
      </div>
    </div>
  );
}