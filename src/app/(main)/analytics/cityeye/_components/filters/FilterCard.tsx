import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { ChevronDown, ChevronUp } from "lucide-react";
import React, { useState } from "react";

interface FilterCardProps {
  title: string;
  children: React.ReactNode;
  className?: string;
  icon?: React.ReactNode;
  iconBgColor?: string;
  collapsible?: boolean;
  defaultExpanded?: boolean;
}

export function FilterCard({
  title,
  children,
  className,
  icon,
  iconBgColor = "bg-blue-100",
  collapsible = false,
  defaultExpanded = true,
}: FilterCardProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  const toggleExpanded = () => {
    if (collapsible) {
      setIsExpanded(!isExpanded);
    }
  };

  return (
    <Card
      className={`shadow-lg border-0 py-0 gap-0 bg-white hover:shadow-xl transition-all duration-300 rounded-xl overflow-hidden ${className}`}>
      <CardHeader
        className={`pb-3 pt-4 px-4 ${collapsible ? "cursor-pointer" : ""} group`}
        onClick={toggleExpanded}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {icon && (
              <div
                className={`p-2 ${iconBgColor} rounded-lg group-hover:scale-110 transition-transform duration-200`}>
                {icon}
              </div>
            )}
            <h3 className="text-sm font-semibold text-slate-700 group-hover:text-slate-900 transition-colors">
              {title}
            </h3>
          </div>
          {collapsible && (
            <div className="text-slate-500 group-hover:text-slate-700 transition-colors">
              {isExpanded ? (
                <ChevronUp className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}
            </div>
          )}
        </div>
      </CardHeader>

      {isExpanded && (
        <CardContent className="px-4 pb-4 pt-0">
          <div className="space-y-2">{children}</div>
        </CardContent>
      )}
    </Card>
  );
}
