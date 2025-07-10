"use client";

import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { useSession } from "next-auth/react";
import dynamic from "next/dynamic"; // Import dynamic
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { deviceService } from "@/services/deviceService";
import { Device } from "@/types/device";
import { Solution } from "@/types/solution";

async function getSolutionDetails(
  solutionId: string,
  accessToken: string
): Promise<Solution | null> {
  const apiUrl = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/solutions/${solutionId}`;
  try {
    const response = await fetch(apiUrl, {
      headers: { Authorization: `Bearer ${accessToken}` },
      cache: "no-store",
    });
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    console.error("Error fetching solution details:", error);
    return null;
  }
}

// import PolygonEditor from "./PolygonSettingsForm";
// Dynamically import the PolygonEditor with SSR turned off
const PolygonEditor = dynamic(() => import("./PolygonSettingsClient"), {
  ssr: false,
  loading: () => <p>Loading map...</p>, // Optional loading component
});

export default function PolygonSettingsPage() {
  const [device, setDevice] = useState<Device | null>(null);
  const [solution, setSolution] = useState<Solution | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const params = useParams();
  const { data: session, status } = useSession();
  const accessToken = session?.accessToken as string;

  const deviceId = params?.deviceId as string;
  const solutionId = params?.solutionId as string;

  useEffect(() => {
    const fetchSolutionDetails = async () => {
      if (!solutionId || !accessToken) return;

      try {
        const fetchedSolution = await getSolutionDetails(
          solutionId,
          accessToken
        );
        if (fetchedSolution) {
          setSolution(fetchedSolution);
        } else {
          setError("Solution not found.");
        }
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "An unknown error occurred."
        );
      }
    };

    fetchSolutionDetails();
  }, [solutionId, accessToken]);

  useEffect(() => {
    // We only need the deviceId to fetch. The apiClient in your service handles auth.
    if (!deviceId) {
      return;
    }

    const fetchDeviceData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        // Use the existing service to fetch the device details
        const deviceData = await deviceService.getDevice(deviceId);
        if (deviceData) {
          setDevice(deviceData);
        } else {
          setError("Device not found.");
        }
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "An unknown error occurred."
        );
      } finally {
        setIsLoading(false);
      }
    };

    fetchDeviceData();
  }, [deviceId]);

  if (isLoading || status === "loading") {
    return (
      <div className="p-6">
        <p>Loading...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <p className="text-red-600">Error: {error}</p>
      </div>
    );
  }

  if (!device) {
    return (
      <div className="p-6">
        <p>Device could not be loaded.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <Breadcrumb className="text-sm text-[#7F8C8D]">
          <BreadcrumbList>
            <BreadcrumbItem className="hover:underline">
              <BreadcrumbLink href="/devices">デバイス</BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator className="text-[#7F8C8D]" />
            <BreadcrumbItem className="hover:underline">
              <BreadcrumbLink href={`/devices/${solutionId}`}>
                {solution?.name}
              </BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator className="text-[#7F8C8D]" />
            <BreadcrumbItem>{device.name}</BreadcrumbItem>
            <BreadcrumbSeparator className="text-[#7F8C8D]" />
            <BreadcrumbItem>ポリゴン設定</BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
        <h1 className="text-2xl font-bold text-[#2C3E50]">ポリゴン設定</h1>
      </div>

      <PolygonEditor device={device} />
    </div>
  );
}
