"use client";

import { useSession } from "next-auth/react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { Suspense, useEffect } from "react";
import { ErrorMessage } from "./_components/ErrorMessage";
import { LoginForm } from "./_components/LoginForm";

export default function LoginPage() {
  // Keep these client-side hooks
  const { status } = useSession();
  const router = useRouter();

  // Redirect logic
  useEffect(() => {
    if (status === "authenticated") {
      router.replace("/users");
    }
  }, [status, router]);

  return (
    <div className="flex min-h-screen w-full">
      {/* Left sidebar */}
      <div className="w-full max-w-md p-8 text-white flex flex-col bg-[#2c5d82]">
        <div className="flex items-center mb-8">
          <Image
            src="/images/media/cybercorelogo_fin_sq_white.png"
            alt="Cybercore"
            width={80}
            height={80}
          />
        </div>

        <h1 className="text-4xl font-bold mb-4">Cybercore Platform</h1>
        <div className="text-lg">
          Centralized control for all your IoT devices and AI solutions across
          multiple clients.
        </div>

        <div className="mt-auto">
          <p className="text-xs text-right mt-8">v1.0.0</p>
        </div>
      </div>

      {/* Right side login form */}
      <div
        className="w-full flex items-center justify-center p-8"
        style={{ backgroundColor: "#f5f7f9" }}
      >
        <LoginForm />
      </div>

      {/* Wrap the search params handling in Suspense */}
      <Suspense fallback={null}>
        <ErrorMessage />
      </Suspense>
    </div>
  );
}
