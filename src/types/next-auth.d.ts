import "next-auth";
import { DefaultSession, DefaultUser } from "next-auth";
import "next-auth/jwt";

// セッションにカスタムフィールドを追加
declare module "next-auth" {
    interface Session {
        accessToken: string;
        user: {
            id: string;
            role: string;
            customerId?: string;
            lastLogin?: string;
            customerName?: string;
        } & DefaultSession["user"];
    }

    // ユーザーにカスタムフィールドを追加
    interface User extends DefaultUser {
        id: string;
        role: string;
        customerId?: string;
        accessToken: string;
        lastLogin?: string;
        customerName?: string;
    }
}

// JWTにカスタムフィールドを追加
declare module "next-auth/jwt" {
    interface JWT {
        id: string;
        role: string;
        customerId?: string;
        accessToken: string;
        lastLogin?: string;
        customerName?: string;
    }
}
