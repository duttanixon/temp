import { Header } from "./_components/Header";
import { Sidebar } from "./_components/Sidebar";
import SessionHandler from "./_components/SessionHandler";
import { auth } from "@/auth";
import { redirect } from "next/navigation";

export default async function MainLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // Get session from server-side auth
  const session = await auth();

  // Redirect to login if not authenticated
  if (!session) {
    redirect("/login");
  }

  return (
    <SessionHandler>
      <div className="min-h-screen flex flex-col bg-slate-900">
        <Header />
        <div className="flex flex-1">
          <Sidebar />
          <main className="flex-1 bg-[#ECF0F1] overflow-auto px-16 py-8">
            {children}
          </main>
        </div>
      </div>
    </SessionHandler>
  );
}
