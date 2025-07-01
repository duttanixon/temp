// src/app/(main)/analytics/cityeye/_components/views/HumanOverviewView.tsx

"use client";

import dynamic from "next/dynamic";

import { ProcessedAnalyticsData } from "@/types/cityeye/cityEyeAnalytics";

const PeopleDirectionMapCard = dynamic(
  () => import("../cards/PeopleDirectionMapCard"),
  { ssr: false }
);

interface PeopleDirectionViewProps {
  processedData: ProcessedAnalyticsData | null;
  isLoading: boolean;
  error: string | null;
  hasAttemptedFetch: boolean;
}

export default function PeopleDirectionView({
  processedData,
  isLoading,
  error,
  hasAttemptedFetch,
}: PeopleDirectionViewProps) {
  console.log("PeopleDirectionView processedData:", processedData);
  return (
    <>
      <PeopleDirectionMapCard
        title="人の動きマップ"
        perDeviceCountsData={{
          detectionZones: [
            {
              name: "北",
              // 北から交差点へ
              In: {
                startPoint: { lat: 39.70238265848726, lng: 141.13896623027466 },
                endPoint: {
                  lat: 39.702860421392586,
                  lng: 141.13856940413172,
                },
                count: 3000,
              },
              //　交差点から北へ
              Out: {
                startPoint: { lat: 39.70266843626451, lng: 141.1389888869297 },
                endPoint: { lat: 39.7024187389318, lng: 141.139224921315 },
                count: 500,
              },
            },
            {
              name: "西",
              // 西から交差点へ
              In: {
                startPoint: {
                  lat: 39.702254530758935,
                  lng: 141.13847210310058,
                },
                endPoint: { lat: 39.70237760081898, lng: 141.13895636964222 },
                count: 8001,
              },
              //　交差点から西へ
              Out: {
                startPoint: { lat: 39.702167828631325, lng: 141.139020861188 },
                endPoint: { lat: 39.70208149720442, lng: 141.1385519389837 },
                count: 6600,
              },
            },
            {
              name: "東",
              // 東から交差点へ
              In: {
                startPoint: { lat: 39.70238423352613, lng: 141.13925812478945 },
                endPoint: { lat: 39.70245139670109, lng: 141.13957994746949 },
                count: 3000,
              },
              // 交差点から東へ
              Out: {
                startPoint: { lat: 39.70230932540181, lng: 141.1396706150676 },
                endPoint: {
                  lat: 39.702218287206264,
                  lng: 141.13933754486698,
                },
                count: 500,
              },
            },

            {
              name: "南",
              // 南から交差点へ
              In: {
                startPoint: { lat: 39.70190912245117, lng: 141.13914579903602 },
                endPoint: { lat: 39.702169002411296, lng: 141.13902804093732 },
                count: 3000,
              },
              // 交差点から南へ
              Out: {
                startPoint: { lat: 39.70223576040819, lng: 141.13935032626014 },
                endPoint: { lat: 39.701925812019304, lng: 141.13945568876954 },
                count: 500,
              },
            },
          ],
        }}
        isLoading={isLoading}
        error={error}
        hasAttemptedFetch={hasAttemptedFetch}
      />
    </>
  );
}
