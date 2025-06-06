"use client";

import { useSidebarContext } from "@/lib/sidebar-context";
import { cn } from "@/lib/utils";

interface MainContentProps {
  children: React.ReactNode;
}

export function MainContent({ children }: MainContentProps) {
  const { isCollapsed } = useSidebarContext();

  return (
    <main
      className={cn(
        "flex-1 bg-[#ECF0F1] overflow-auto px-6 py-6 transition-all duration-300",
        isCollapsed ? "ml-16" : "ml-64"
      )}>
      {children}
    </main>
  );
}
