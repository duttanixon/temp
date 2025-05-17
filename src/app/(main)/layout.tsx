import { Header } from "./_components/Header";
import { Sidebar } from "./_components/Sidebar";
import { MainContent } from "./_components/MainContent";
import SessionHandler from "./_components/SessionHandler";
import { auth } from "@/auth";
import { redirect } from "next/navigation";
import { Toaster } from "sonner";
import { SidebarProvider } from "@/lib/sidebar-context";

export default async function MainLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  console.log("📂 MAIN LAYOUT: Initializing main layout (server component)");
  // Get session from server-side auth
  const session = await auth();
  console.log("📂 MAIN LAYOUT: Session exists:", !!session);

  // Redirect to login if not authenticated
  if (!session) {
    console.log("📂 MAIN LAYOUT: No session, redirecting to login");
    redirect("/login");
  }

  console.log("📂 MAIN LAYOUT: Session valid, rendering main layout");
  return (
    <SidebarProvider>
      <SessionHandler>
        <div className="min-h-screen flex flex-col bg-slate-900">
          <Header />
          <div className="flex flex-1">
            <Sidebar />
            <main className="flex-1 bg-[#ECF0F1] overflow-auto px-16 py-8">
              <MainContent>{children}</MainContent>
              <Toaster position="bottom-left" richColors />
            </main>
          </div>
        </div>
      </SessionHandler>
    </SidebarProvider>
  );
}
