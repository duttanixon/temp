import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface FilterCardProps {
  title: string;
  children: React.ReactNode;
  className?: string;
}

export function FilterCard({ title, children, className }: FilterCardProps) {
  return (
    <Card className={`shadow-sm border-[#E0E0E0] ${className}`}>
      <CardHeader className="pb-2 pt-3 px-4">
        <CardTitle className="text-sm font-semibold text-gray-700">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="px-4 pb-3">
        {children}
      </CardContent>
    </Card>
  );
}