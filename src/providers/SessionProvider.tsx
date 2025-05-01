"use client";

import { SessionProvider as NextAuthSessionProvider } from "next-auth/react";
import { ReactNode } from "react";

// SessionProviderのプロパティ型定義
interface SessionProviderProps {
    children: ReactNode;
}

// セッションプロバイダーコンポーネント
const SessionProvider = ({ children }: SessionProviderProps) => {
    return <NextAuthSessionProvider>{children}</NextAuthSessionProvider>;
};

export default SessionProvider;
