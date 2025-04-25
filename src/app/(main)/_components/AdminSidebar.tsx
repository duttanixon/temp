"use client";

import {
    AlertCircle,
    AppWindowMacIcon,
    ArrowRight,
    BarChart2,
    Building,
    Database,
    LayoutDashboard,
    LightbulbIcon,
    WrenchIcon,
} from "lucide-react";
import Link from "next/link";

const menuItems = [
    { name: "Dashboard", icon: LayoutDashboard, href: "/dashboard" },
    { name: "Devices", icon: Database, href: "/devices" },
    { name: "Customers", icon: Building, href: "/customers" },
    { name: "Solutions", icon: LightbulbIcon, href: "/solutions" },
    { name: "Analytics", icon: BarChart2, href: "/analytics" },
    { name: "Alerts", icon: AlertCircle, href: "/alerts" },
    { name: "Maintenance", icon: WrenchIcon, href: "/maintenance" },
    { name: "Administration", icon: AppWindowMacIcon, href: "", isDiv: true },
];

// 管理メニュー項目（サブメニュー付き）
const adminMenuItems = [
    { name: "User Management", icon: ArrowRight, href: "/users" },
    { name: "System Settings", icon: ArrowRight, href: "/settings" },
    { name: "Audit Logs", icon: ArrowRight, href: "/logs" },
];

export function AdminSidebar() {
    return (
        <aside className="w-64 bg-[#34495E] text-white flex flex-col">
            <div className="px-4 py-6">
                <nav className="space-y-1">
                    {menuItems.map((item) => {
                        const Icon = item.icon;

                        if (item.isDiv) {
                            return (
                                <div
                                    key={item.name}
                                    className="flex items-center gap-3 px-4 py-3 rounded-lg transition-colors text-slate-300">
                                    <Icon className="h-5 w-5" />
                                    <span>{item.name}</span>
                                </div>
                            );
                        }

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
                    {adminMenuItems.map((item) => {
                        const Icon = item.icon;

                        return (
                            <Link
                                key={item.name}
                                href={item.href}
                                className="flex items-center gap-3 pl-8 py-3 rounded-lg transition-colors text-slate-300 hover:bg-slate-700 hover:text-white">
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
