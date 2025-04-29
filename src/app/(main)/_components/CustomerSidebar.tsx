"use client";

import {
    AlertCircle,
    BarChart2,
    Database,
    HeadphonesIcon,
    LayoutDashboard,
    Users,
} from "lucide-react";
import Link from "next/link";

const menuItems = [
    { name: "ダッシュボード", icon: LayoutDashboard, href: "/dashboard" },
    { name: "デバイス", icon: Database, href: "/devices" },
    { name: "分析", icon: BarChart2, href: "/analytics" },
    { name: "通知", icon: AlertCircle, href: "/alerts" },
    { name: "サポート", icon: HeadphonesIcon, href: "/support" },
    { name: "ユーザー管理", icon: Users, href: "/users", active: true },
];

export function CustomerSidebar() {
    return (
        <aside className="w-64 bg-[#34495E] text-white flex flex-col">
            <div className="px-4 py-6">
                <nav className="space-y-1">
                    {menuItems.map((item) => {
                        const Icon = item.icon;

                        return (
                            <Link
                                key={item.name}
                                href={item.href}
                                className="flex items-center gap-3 px-4 py-3 rounded-lg transition-colors text-slate-300 hover:bg-slate-700 hover:text-white">
                                <Icon className="h-5 w-5" />
                                <span>{item.name}</span>
                            </Link>
                        );
                    })}
                </nav>
            </div>
        </aside>
    );
}
