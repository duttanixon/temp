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
    { name: "ダッシュボード", icon: LayoutDashboard, href: "/dashboard" },
    { name: "デバイス", icon: Database, href: "/devices" },
    { name: "顧客", icon: Building, href: "/customers" },
    { name: "ソリューション", icon: LightbulbIcon, href: "/solutions" },
    { name: "分析", icon: BarChart2, href: "/analytics" },
    { name: "通知", icon: AlertCircle, href: "/alerts" },
    { name: "メンテナンス", icon: WrenchIcon, href: "/maintenance" },
    { name: "管理", icon: AppWindowMacIcon, href: "", isDiv: true },
];

// 管理メニュー項目（サブメニュー付き）
const adminMenuItems = [
    { name: "ユーザー管理", icon: ArrowRight, href: "/users" },
    { name: "システム設定", icon: ArrowRight, href: "/settings" },
    { name: "ログ", icon: ArrowRight, href: "/logs" },
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
