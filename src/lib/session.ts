import { auth } from "@/auth";

export type SessionUser = {
  id: string;
  email: string;
  role: string;
  customerId?: string;
  customerName?: string;
  firstName?: string;
  lastName?: string;
  accessToken?: string;
};

export type SessionData = {
  user: SessionUser | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  isCustomerAdmin: boolean;
  isCustomerUser: boolean;
};

export async function getSessionData(): Promise<SessionData> {
  const session = await auth();

  if (!session?.user) {
    return {
      user: null,
      isAuthenticated: false,
      isAdmin: false,
      isCustomerAdmin: false,
      isCustomerUser: false,
    };
  }

  return {
    user: session.user as SessionUser,
    isAuthenticated: true,
    isAdmin: session.user.role === "ADMIN",
    isCustomerAdmin: session.user.role === "CUSTOMER_ADMIN",
    isCustomerUser: session.user.role === "CUSTOMER_USER",
  };
}
