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
import { SidebarBase, MenuItem, MenuSection } from "./SidebarBase";

export function AdminSidebar() {
  const sections: MenuSection[] = [
    {
      items: [
        { href: "/dashboard", icon: LayoutDashboard, label: "ダッシュボード" },
        { href: "/devices", icon: Database, label: "デバイス" },
        { href: "/customers", icon: Building, label: "顧客" },
        { href: "/solutions", icon: LightbulbIcon, label: "ソリューション" },
        { href: "/analytics", icon: BarChart2, label: "分析" },
        { href: "/alerts", icon: AlertCircle, label: "通知" },
        { href: "/maintenance", icon: WrenchIcon, label: "メンテナンス" },
      ],
    },
    {
      title: "管理",
      items: [
        { href: "/users", icon: Users, label: "ユーザー管理" },
        { href: "/settings", icon: Settings, label: "システム設定" },
        { href: "/logs", icon: FileText, label: "ログ" },
      ],
    },
  ];

  return <SidebarBase sections={sections} />;
}
