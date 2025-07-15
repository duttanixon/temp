"use client";

import {
  LayoutDashboard,
  Database,
  Building,
  LightbulbIcon,
  BarChart2,
  AlertCircle,
  WrenchIcon,
  Users,
  Settings,
  FileText,
} from "lucide-react";
import { SidebarBase, MenuSection } from "./SidebarBase";

export function AdminSidebar() {
  const sections: MenuSection[] = [
    {
      items: [
        { href: "/dashboard", icon: LayoutDashboard, label: "ダッシュボード" },
        { href: "/analytics", icon: BarChart2, label: "分析" },
        { href: "/alerts", icon: AlertCircle, label: "通知" },
      ],
    },
    {
      title: "管理",
      items: [
        { href: "/devices", icon: Database, label: "デバイス" },
        { href: "/solutions", icon: LightbulbIcon, label: "ソリューション" },
        { href: "/customers", icon: Building, label: "顧客" },
        { href: "/users", icon: Users, label: "ユーザー" },
        { href: "/maintenance", icon: WrenchIcon, label: "メンテナンス" },
        { href: "/settings", icon: Settings, label: "システム設定" },
        { href: "/audit-logs", icon: FileText, label: "ログ" },
      ],
    },
  ];

  return <SidebarBase sections={sections} />;
}
