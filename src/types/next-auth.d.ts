import "next-auth";
import { DefaultSession, DefaultUser } from "next-auth";
import "next-auth/jwt";

// セッションにカスタムフィールドを追加
declare module "next-auth" {
  interface Session {
    accessToken: string;
    error?: string;
    tokenExpires?: number;
    user: {
      id: string;
      role: string;
      customerId?: string;
      lastLogin?: string;
      customerName?: string;
      firstName?: string;
      lastName?: string;
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
    firstName?: string;
    lastName?: string;
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
    firstName?: string;
    lastName?: string;
    tokenExpires?: number;
    error?: string;
  }
}
