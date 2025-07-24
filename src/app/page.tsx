import { auth } from "@/auth";
import { redirect } from "next/navigation";

export default async function HomePage() {
  // Get the current session
  const session = await auth();
  
  // If user is logged in, redirect to /login (which will redirect to /users)
  if (session && !session.error) {
    console.log("🏠 HOME: User is authenticated, redirecting to /login");
    redirect("/login");
  }
  
  // If user is not logged in, redirect to login page
  console.log("🏠 HOME: User not authenticated, redirecting to /login");
  redirect("/login");
}