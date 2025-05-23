"use client";

import {
  LayoutDashboard,
  Database,
  BarChart2,
  AlertCircle,
  HeadphonesIcon,
  Users,
} from "lucide-react";
import { SidebarBase, MenuSection } from "./SidebarBase";

export function CustomerSidebar() {
  const sections: MenuSection[] = [
    {
      items: [
        { href: "/dashboard", icon: LayoutDashboard, label: "ダッシュボード" },
        { href: "/devices", icon: Database, label: "デバイス" },
        { href: "/analytics", icon: BarChart2, label: "分析" },
        { href: "/alerts", icon: AlertCircle, label: "通知" },
        { href: "/support", icon: HeadphonesIcon, label: "サポート" },
      ],
    },
    {
      items: [{ href: "/users", icon: Users, label: "ユーザー管理" }],
    },
  ];

  return <SidebarBase sections={sections} />;
}
