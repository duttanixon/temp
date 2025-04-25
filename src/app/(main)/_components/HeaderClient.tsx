"use client";

// HeaderClient.tsx
import { Button } from "@/components/ui/button";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { User } from "lucide-react";
import { signOut } from "next-auth/react";
import { useRouter } from "next/navigation";

interface HeaderClientProps {
    userName: string;
    userRole: string;
    customerName: string;
    isSubHeaderView: boolean;
    isAuthenticated: boolean;
}

export function HeaderClient({
    userName,
    userRole,
    customerName,
    isSubHeaderView,
    isAuthenticated,
}: HeaderClientProps) {
    const router = useRouter();

    // ログアウト処理
    const handleLogout = async () => {
        await signOut({ redirect: false });
        router.push("/login");
    };

    return (
        <div>
            <header className="bg-[#2C3E50] text-white px-8 py-2 flex items-center justify-between">
                <h1 className="text-xl font-semibold">
                    IoT Edge Device Portal
                </h1>
                {isAuthenticated && (
                    <div className="flex items-center gap-4">
                        <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                                <Button
                                    variant="ghost"
                                    className="flex items-center gap-2 text-white cursor-pointer">
                                    <User className="h-5 w-5" />
                                    <span>{userName || "User"} ▾</span>
                                </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                                <DropdownMenuItem
                                    onClick={() => router.push("/profile")}
                                    className="cursor-pointer">
                                    Profile
                                </DropdownMenuItem>
                                <DropdownMenuItem
                                    onClick={() => router.push("/settings")}
                                    className="cursor-pointer">
                                    Settings
                                </DropdownMenuItem>
                                <DropdownMenuItem
                                    onClick={handleLogout}
                                    className="cursor-pointer text-red-500 hover:text-red-700">
                                    Logout
                                </DropdownMenuItem>
                            </DropdownMenuContent>
                        </DropdownMenu>
                    </div>
                )}
            </header>
            {/* サブヘッダー - 顧客ユーザー向け */}
            {isSubHeaderView && (
                <div className="bg-[#34495E] text-white px-8 py-2 border-t border-gray-700">
                    <h2 className="text-lg font-medium">
                        {customerName} Portal
                    </h2>
                </div>
            )}
        </div>
    );
}
