"use client";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useSidebarContext } from "@/lib/sidebar-context"; // Add this import
import { Menu, User } from "lucide-react";
import { signOut } from "next-auth/react";
import { useRouter } from "next/navigation";

interface HeaderClientProps {
  userName: string;
  customerName: string;
  isSubHeaderView: boolean;
  isAuthenticated: boolean;
}

export function HeaderClient({
  userName,
  customerName,
  isSubHeaderView,
  isAuthenticated,
}: HeaderClientProps) {
  const router = useRouter();
  const { toggleSidebar } = useSidebarContext(); // Use the sidebar context

  // Logout handler
  const handleLogout = async () => {
    await signOut({ redirect: false });
    router.push("/login");
  };

  return (
    <div className="sticky top-0 z-20">
      <header
        className="bg-[color:var(--header-bg)] text-[color:var(--header-text)] px-4 sm:px-8 py-3 flex items-center justify-between"
        style={{ boxShadow: "0 1px 3px rgba(0,0,0,0.1)" }}
      >
        <div className="flex items-center gap-3">
          {/* Add sidebar toggle button */}
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleSidebar}
            className="text-[color:var(--header-text)] hover:bg-[color:var(--header-hover)] mr-2"
          >
            <Menu className="h-5 w-5" />
            <span className="sr-only">Toggle sidebar</span>
          </Button>
          {isSubHeaderView ? (
            <h1 className="text-xl font-semibold">{customerName}</h1>
          ) : (
            <h1 className="text-xl font-semibold">
              IoT エッジデバイス管理システム
            </h1>
          )}
        </div>

        {isAuthenticated && (
          <div className="flex items-center gap-4">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  className="flex items-center gap-2 text-[color:var(--header-text)] hover:bg-[color:var(--header-hover)] cursor-pointer"
                >
                  <User className="h-5 w-5" />
                  <span>{userName || "User"} ▾</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem
                  onClick={() => router.push("/profile")}
                  className="cursor-pointer"
                >
                  Profile
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => router.push("/settings")}
                  className="cursor-pointer"
                >
                  Settings
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={handleLogout}
                  className="cursor-pointer text-[color:var(--danger-500)] hover:text-[color:var(--danger-600)]"
                >
                  Logout
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        )}
      </header>
    </div>
  );
}
