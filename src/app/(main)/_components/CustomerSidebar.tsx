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
        { href: "/analytics", icon: BarChart2, label: "分析" },
        { href: "/alerts", icon: AlertCircle, label: "通知" },
        { href: "/support", icon: HeadphonesIcon, label: "サポート" },
      ],
    },
    {
      title: "管理",
      items: [
        { href: "/devices", icon: Database, label: "デバイス" },
        { href: "/users", icon: Users, label: "ユーザー" },
      ],
    },
  ];

  return <SidebarBase sections={sections} />;
}
