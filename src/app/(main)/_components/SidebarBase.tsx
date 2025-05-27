"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSidebarContext } from "@/lib/sidebar-context";
import { cn } from "@/lib/utils";
import { Separator } from "@/components/ui/separator";
import { LucideIcon } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

// Types for menu items
export interface MenuItem {
  href: string;
  icon: LucideIcon;
  label: string;
  isSubmenu?: boolean;
}

// Types for section with multiple menu items
export interface MenuSection {
  title?: string;
  items: MenuItem[];
}

interface SidebarBaseProps {
  sections: MenuSection[];
}

export function SidebarBase({ sections }: SidebarBaseProps) {
  const pathname = usePathname();
  const { isCollapsed } = useSidebarContext();

  // Helper function to determine if a menu item is active
  const isActive = (href: string) => {
    return pathname === href || pathname.startsWith(`${href}/`);
  };

  // Function to render a menu item with proper active state and styling
  const renderMenuItem = ({
    href,
    icon: Icon,
    label,
    isSubmenu = false,
  }: MenuItem) => {
    const active = isActive(href);

    const itemClasses = cn(
      "flex items-center gap-3 px-3 py-2 mb-2 rounded-md transition-colors relative group",
      isSubmenu ? "pl-9" : "",
      active
        ? "bg-[#437A9E] text-[#FFFFFF]"
        : "text-[#FFFFFF] hover:bg-[#437A9E] opacity-50"
    );

    // If collapsed, show tooltip with the label
    if (isCollapsed) {
      return (
        <TooltipProvider key={href}>
          <Tooltip delayDuration={0}>
            <TooltipTrigger asChild>
              <Link href={href} className={itemClasses}>
                <Icon className="h-5 w-5 shrink-1" />
                {active && (
                  <div className="absolute w-1 h-7 bg-[color:var(--sidebar-item-active)] rounded-full left-0" />
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
      <Link key={href} href={href} className={itemClasses}>
        <Icon className="h-5 w-5 shrink-0" />
        <span className="truncate">{label}</span>
        {/* {active && (
          <div className="absolute w-1 h-7 bg-[color:var(--sidebar-item-active)] rounded-full left-0" />
        )} */}
      </Link>
    );
  };

  return (
    <aside
      className={cn(
        "bg-[#34495E] border-r border-[color:var(--sidebar-border)] transition-all duration-300 fixed inset-y-0 left-0 flex flex-col",
        "top-13",
        "z-10",
        isCollapsed ? "w-16" : "w-64"
      )}
    >
      <div className="flex-1 px-3 py-4 space-y-2 overflow-y-auto scrollbar-thin">
        {sections.map((section, index) => (
          <div key={index}>
            {index > 0 && <Separator className="my-4" />}

            {!isCollapsed && section.title && (
              <div className="flex items-center justify-between gap-3 px-3 py-2 mb-2 rounded-md text-normal font-bold text-[#FFFFFF] cursor-pointer select-none">
                {section.title}
              </div>
            )}

            <div className="space-y-1">
              {section.items.map((item) => renderMenuItem(item))}
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
}
