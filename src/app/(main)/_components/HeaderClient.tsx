"use client";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useSidebarContext } from "@/lib/sidebar-context";
import { Menu, User } from "lucide-react";
import { signOut } from "next-auth/react";
import { useRouter } from "next/navigation";

interface HeaderClientProps {
  userName: string;
  customerName: string;
  showCustomerHeader: boolean;
  isAuthenticated: boolean;
}

export function HeaderClient({
  userName,
  customerName,
  showCustomerHeader,
  isAuthenticated,
}: HeaderClientProps) {
  const router = useRouter();
  const { toggleSidebar } = useSidebarContext();

  // Logout handler
  const handleLogout = async () => {
    await signOut({ redirect: false });
    router.push("/login");
  };

  return (
    <div className="sticky top-0 z-20">
      <header
        className="bg-[color:var(--header-bg)] text-[color:var(--header-text)] px-4 sm:px-4 py-2 flex items-center justify-between "
        style={{ boxShadow: "0 1px 3px rgba(0,0,0,0.1)" }}
      >
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleSidebar}
            className="text-[color:var(--header-text)] hover:bg-[color:var(--header-hover)] mr-1"
          >
            <Menu className="h-5 w-5" />
            <span className="sr-only">Toggle sidebar</span>
          </Button>

          <h1 className="text-xl font-semibold">
            {showCustomerHeader
              ? `IoT エッジデバイス管理システム - ${customerName}`
              : "IoT エッジデバイス管理システム"}
          </h1>
        </div>

        {isAuthenticated && (
          <UserMenu userName={userName} onLogout={handleLogout} />
        )}
      </header>
    </div>
  );
}

// User menu component extracted for better separation of concerns
function UserMenu({
  userName,
  onLogout,
}: {
  userName: string;
  onLogout: () => void;
}) {
  const router = useRouter();

  return (
    <div className="flex items-center gap-4">
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            className="flex items-center gap-2 text-[color:var(--header-text)] hover:bg-[color:var(--header-hover)] cursor-pointer"
          >
            <User className="h-5 w-5" />
            <span className="text-sm">{userName} ▾</span>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem
            onClick={() => router.push("/profile")}
            className="cursor-pointer"
          >
            プロフィール
          </DropdownMenuItem>
          <DropdownMenuItem
            onClick={() => router.push("/settings")}
            className="cursor-pointer"
          >
            設定
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem
            onClick={onLogout}
            className="cursor-pointer text-[color:var(--danger-500)] hover:text-[color:var(--danger-600)]"
          >
            ログアウト
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
