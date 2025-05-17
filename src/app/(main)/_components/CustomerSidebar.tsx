"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSidebarContext } from "@/lib/sidebar-context";
import { cn } from "@/lib/utils";
import { Separator } from "@/components/ui/separator";
import {
  LayoutDashboard,
  Database,
  BarChart2,
  AlertCircle,
  HeadphonesIcon,
  Users,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

export function CustomerSidebar() {
  const pathname = usePathname();
  const { isCollapsed, toggleSidebar } = useSidebarContext();

  // Helper function to determine if a menu item is active
  const isActive = (href: string) => {
    return pathname === href || pathname.startsWith(`${href}/`);
  };

  // Function to render a menu item with proper active state and styling
  const MenuItem = ({
    href,
    icon: Icon,
    label,
  }: {
    href: string;
    icon: any;
    label: string;
  }) => {
    const active = isActive(href);

    const itemClasses = cn(
      "flex items-center gap-3 px-3 py-2 rounded-md transition-colors relative group",
      active
        ? "bg-accent text-accent-foreground"
        : "text-muted-foreground hover:bg-accent/50 hover:text-accent-foreground"
    );

    // If collapsed, show tooltip with the label
    if (isCollapsed) {
      return (
        <TooltipProvider>
          <Tooltip delayDuration={0}>
            <TooltipTrigger asChild>
              <Link href={href} className={itemClasses}>
                <Icon className="h-5 w-5 shrink-0" />
                {active && (
                  <div className="absolute w-1 h-7 bg-primary rounded-full left-0" />
                )}
              </Link>
            </TooltipTrigger>
            <TooltipContent side="right" className="ml-1">
              {label}
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      );
    }

    // Regular item (not collapsed)
    return (
      <Link href={href} className={itemClasses}>
        <Icon className="h-5 w-5 shrink-0" />
        <span className="truncate">{label}</span>
        {active && (
          <div className="absolute w-1 h-7 bg-primary rounded-full left-0" />
        )}
      </Link>
    );
  };

  return (
    <aside
      className={cn(
        // Keep existing classes
        "bg-card border-r border-border/40 transition-all duration-300 fixed inset-y-0 left-0 flex flex-col",
        // Change these values:
        "top-16", // Start below header (assuming header height is 4rem/64px)
        "z-10", // Lower z-index than header
        isCollapsed ? "w-16" : "w-64"
      )}
    >
      <div className="flex-1 px-3 py-4 space-y-2 overflow-y-auto scrollbar-thin">
        <div className="space-y-1">
          <MenuItem
            href="/dashboard"
            icon={LayoutDashboard}
            label="ダッシュボード"
          />
          <MenuItem href="/devices" icon={Database} label="デバイス" />
          <MenuItem href="/analytics" icon={BarChart2} label="分析" />
          <MenuItem href="/alerts" icon={AlertCircle} label="通知" />
          <MenuItem href="/support" icon={HeadphonesIcon} label="サポート" />
        </div>

        <Separator className="my-4" />

        <div className="space-y-1">
          <MenuItem href="/users" icon={Users} label="ユーザー管理" />
        </div>
      </div>
    </aside>
  );
}
