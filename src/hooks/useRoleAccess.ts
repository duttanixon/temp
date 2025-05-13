// // src/hooks/useRoleAccess.ts
// import { useSession } from "next-auth/react";

// export function useRoleAccess() {
//   const { data: session } = useSession();

//   // Get user role or default to empty string
//   const role = session?.user?.role || "";

//   return {
//     isAuthenticated: !!session?.user,
//     isAdmin: role === "ADMIN",
//     isEngineer: role === "ENGINEER",
//     isCustomerAdmin: role === "CUSTOMER_ADMIN",
//     isCustomerUser: role === "CUSTOMER_USER",
//     canAccessAdminFeatures: role === "ADMIN" || role === "ENGINEER",
//     canAccessCustomerFeatures:
//       role === "CUSTOMER_ADMIN" || role === "CUSTOMER_USER",
//     role,
//   };
// }
