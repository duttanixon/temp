"use client";

import {
  BarChart2,
  Database,
  FileText,
  LightbulbIcon,
  Users,
} from "lucide-react";
import { MenuSection, SidebarBase } from "./SidebarBase";

export function CustomerSidebar() {
  const sections: MenuSection[] = [
    {
      items: [
        // { href: "/dashboard", icon: LayoutDashboard, label: "ダッシュボード" },
        { href: "/analytics", icon: BarChart2, label: "分析" },
        // { href: "/alerts", icon: AlertCircle, label: "通知" },
        // { href: "/support", icon: HeadphonesIcon, label: "サポート" },
      ],
    },
    {
      title: "管理",
      items: [
        { href: "/devices", icon: Database, label: "デバイス" },
        { href: "/solutions", icon: LightbulbIcon, label: "ソリューション" },
        { href: "/users", icon: Users, label: "ユーザー" },
        { href: "/audit-logs", icon: FileText, label: "ログ" },
      ],
    },
  ];

  return <SidebarBase sections={sections} />;
}
