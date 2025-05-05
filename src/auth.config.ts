import type { NextAuthConfig } from "next-auth";

export const authConfig = {
  pages: {
    signIn: "/login",
  },
  callbacks: {
    authorized({ auth, request: { nextUrl } }) {
      const isLoggedIn = !!auth?.user;
      const isAuthPage = nextUrl.pathname.startsWith("/login");

      // Redirect authenticated users away from auth pages
      if (isAuthPage) {
        if (isLoggedIn) {
          return Response.redirect(new URL("/", nextUrl));
        }
        return true;
      }

      // Require authentication for other pages
      if (!isLoggedIn) {
        return false; // Redirects to login
      }

      return true;
    },
  },
  providers: [],
} satisfies NextAuthConfig;

// import type { NextAuthConfig } from 'next-auth';

// export const authConfig = {
//   pages: {
//     signIn: '/login',
//   },
//   callbacks: {
//     authorized({ auth, request: { nextUrl } }) {
//       const isLoggedIn = !!auth?.user;
//       const isAuthPage = nextUrl.pathname === '/login';

//       // Allow access to login page when not logged in
//       if (isAuthPage) {
//         return true;
//       }

//       // Require authentication for all other pages
//       return isLoggedIn;
//     }
//   },
//   providers: [],
// } satisfies NextAuthConfig;
