"use client";

import "@/app/globals.css";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { Toaster } from "sonner";
import { LoginForm } from "./_components/LoginForm";

export default function LoginPage() {
  const { status } = useSession();
  const router = useRouter();

  // Much simpler redirect logic
  useEffect(() => {
    if (status === "authenticated") {
      router.replace("/");
    }
  }, [status, router]);

  return (
    <div className="flex min-h-screen w-full">
      {/* 左側のサイドバー */}
      <div
        className="w-full max-w-md p-8 text-white flex flex-col"
        style={{ backgroundColor: "#2c5d82" }}
      >
        <div className="flex items-center mb-8">
          <div className="h-20 w-20 rounded-full bg-white flex items-center justify-center">
            <span className="text-3xl font-bold" style={{ color: "#3498db" }}>
              EM
            </span>
          </div>
        </div>

        <h1 className="text-4xl font-bold mb-4">
          Edge Device Management System
        </h1>
        <p className="text-lg">
          Centralized control for all your IoT devices and AI solutions across
          multiple clients.
        </p>

        <div className="mt-auto">
          <p className="text-xs text-right mt-8">v1.0.0</p>
        </div>
      </div>

      {/* 右側のログインフォーム */}
      <div
        className="w-full flex items-center justify-center p-8"
        style={{ backgroundColor: "#f5f7f9" }}
      >
        <LoginForm />
      </div>
      {/* Sonnerのトースターコンポーネントを追加 */}
      <Toaster richColors closeButton position="bottom-left" />
    </div>
  );
}
