"use client";

import { SolutionPackage } from "@/types/package";
import { formatDate } from "@/utils/dateUtils";
import { Package, Clock, Upload } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Button } from "@/components/ui/button";
import { useState } from "react";

interface PackageListProps {
  packages: SolutionPackage[];
  loading?: boolean;
  onDeploy: (packageId: string) => void;
  isDeploying: boolean;
}

/**
 * Component to display list of packages
 * Follows Single Responsibility - only handles package display logic
 */
export default function PackageList({
  packages,
  loading = false,
  onDeploy,
  isDeploying,
}: PackageListProps) {
  const [activePackageId, setActivePackageId] = useState<string | null>(null);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#3498DB]" />
      </div>
    );
  }

  if (packages.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-[#7F8C8D]">
        <Package className="h-12 w-12 mb-3 opacity-50" />
        <p className="text-sm">No packages available for this solution</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {packages.map((pkg) => (
        <div
          key={pkg.package_id}
          className="bg-white border border-[#E0E0E0] rounded-lg p-4 hover:shadow-md transition-shadow flex items-center justify-between"
        >
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <Package className="h-5 w-5 text-[#3498DB]" />
              <h3 className="font-medium text-[#2C3E50]">{pkg.name}</h3>
              <span className="text-xs bg-[#ECF0F1] text-[#7F8C8D] px-2 py-1 rounded">
                v{pkg.version}
              </span>
            </div>

            <p className="text-sm text-[#7F8C8D] mb-3">
              {pkg.description || "No description available"}
            </p>

            <div className="flex items-center gap-4 text-xs text-[#95A5A6]">
              {pkg.created_at && (
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        <span>Created: {formatDate(pkg.created_at)}</span>
                      </div>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>{new Date(pkg.created_at).toLocaleString()}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}

              {pkg.model_associations.length > 0 && (
                <div className="flex items-center gap-1">
                  <span className="font-medium">
                    {pkg.model_associations.length} model(s) associated
                  </span>
                </div>
              )}
            </div>
          </div>
          <Button
            onClick={() => {
              setActivePackageId(pkg.package_id);
              onDeploy(pkg.package_id);
            }}
            size="sm"
            disabled={isDeploying && activePackageId === pkg.package_id}
            className="flex items-center gap-2"
          >
            <Upload className="h-4 w-4" />
            {isDeploying && activePackageId === pkg.package_id
              ? "Deploying..."
              : "Deploy"}
          </Button>
        </div>
      ))}
    </div>
  );
}
