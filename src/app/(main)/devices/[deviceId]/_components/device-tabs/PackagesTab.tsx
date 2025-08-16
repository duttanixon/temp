"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { packageService } from "@/services/packageService";
import { deviceService } from "@/services/deviceService";
import { SolutionPackage } from "@/types/package";
import { Device } from "@/types/device";
import PackageList from "./packages/PackageList";
import PackageFilters from "./packages/PackageFilters";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle } from "lucide-react";
import { toast } from "sonner";

/**
 * Main Packages Tab Component
 * Orchestrates package fetching and display for a device's solution
 */
export default function PackagesTab() {
  const params = useParams();
  const deviceId = params.deviceId as string;

  const [packages, setPackages] = useState<SolutionPackage[]>([]);
  const [filteredPackages, setFilteredPackages] = useState<SolutionPackage[]>(
    []
  );
  const [device, setDevice] = useState<Device | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // state for deployment
  const [isDeploying, setIsDeploying] = useState(false);

  // Filter states
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState<"name" | "version" | "date">("date");

  // Fetch device details to get solution information
  useEffect(() => {
    const fetchDeviceAndPackages = async () => {
      try {
        setLoading(true);
        setError(null);

        // First, get device details to know which solution it's using
        const deviceData = await deviceService.getDevice(deviceId);
        if (!deviceData) {
          throw new Error("Device not found");
        }
        setDevice(deviceData);

        // Then fetch packages for that solution
        if (deviceData.solution_name) {
          const packagesResponse = await packageService.getPackages({
            solution_name: deviceData.solution_name,
          });
          setPackages(packagesResponse.packages);
          setFilteredPackages(packagesResponse.packages);
        }
      } catch (err) {
        console.error("Failed to fetch packages:", err);
        setError(
          err instanceof Error ? err.message : "Failed to load packages"
        );
      } finally {
        setLoading(false);
      }
    };

    if (deviceId) {
      fetchDeviceAndPackages();
    }
  }, [deviceId]);

  // Apply filters and sorting
  useEffect(() => {
    let filtered = [...packages];

    // Apply search filter
    if (searchQuery) {
      filtered = filtered.filter(
        (pkg) =>
          pkg.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          pkg.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
          pkg.version.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Apply sorting
    filtered.sort((a, b) => {
      switch (sortBy) {
        case "name":
          return a.name.localeCompare(b.name);
        case "version":
          return a.version.localeCompare(b.version);
        case "date":
          const dateA = new Date(a.created_at || 0).getTime();
          const dateB = new Date(b.created_at || 0).getTime();
          return dateB - dateA; // Newest first
        default:
          return 0;
      }
    });

    setFilteredPackages(filtered);
  }, [packages, searchQuery, sortBy]);

  const handleRefresh = async () => {
    if (device?.solution_name) {
      try {
        setLoading(true);
        const packagesResponse = await packageService.getPackages({
          solution_name: device.solution_name,
        });
        setPackages(packagesResponse.packages);
      } catch (err) {
        console.error("Failed to refresh packages:", err);
      } finally {
        setLoading(false);
      }
    }
  };

  const handleDeploy = async (packageId: string) => {
    setIsDeploying(true);
    try {
      if (!deviceId) {
        throw new Error("Device ID is missing.");
      }
      await packageService.deployPackage(packageId, [deviceId]);
      toast.success("Deployment initiated successfully!", {
        description: `Package ${packageId} is being deployed to device ${deviceId}.`,
      });
    } catch (err) {
      console.error("Failed to deploy package:", err);
      toast.error("Deployment Failed", {
        description:
          err instanceof Error ? err.message : "An unexpected error occurred.",
      });
    } finally {
      setIsDeploying(false);
    }
  };

  if (error) {
    return (
      <div className="bg-white p-6 min-h-[300px] rounded-b-lg">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 min-h-[300px] rounded-b-lg">
      <div className="space-y-4">
        {/* Header Section */}
        <div className="flex items-center justify-between border-b pb-4">
          <div>
            <h3 className="text-lg font-semibold text-[#2C3E50]">
              Available Packages
            </h3>
            {device && (
              <p className="text-sm text-[#7F8C8D] mt-1">
                Solution: {device.solution_name} (v{device.solution_version})
              </p>
            )}
          </div>
        </div>

        {/* Filters and Package List */}
        <PackageFilters
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          sortBy={sortBy}
          onSortChange={setSortBy}
          onRefresh={handleRefresh}
          totalCount={filteredPackages.length}
        />
        <PackageList
          packages={filteredPackages}
          loading={loading}
          onDeploy={handleDeploy}
          isDeploying={isDeploying}
        />
      </div>
    </div>
  );
}
