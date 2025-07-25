import { Input } from "@/components/ui/input";
import { Search } from "lucide-react";

type Props = {
  deviceType: string;
  setDeviceType: (val: string) => void;
  status: string;
  setStatus: (val: string) => void;
  query: string;
  setQuery: (val: string) => void;
};

export default function SolutionFilters({
  deviceType,
  setDeviceType,
  status,
  setStatus,
  query,
  setQuery,
}: Props) {
  return (
    <div className="inline-block border border-gray-400 rounded-md px-4 py-3 bg-white overflow-hidden">
      <div className="flex items-center gap-6 flex-wrap">
        <div className="flex items-center gap-2">
          <label className="text-gray-800 text-sm whitespace-nowrap">
            互換デバイス:
          </label>
          <div className="w-40">
            <select
              value={deviceType}
              onChange={(e) => setDeviceType(e.target.value)}
              className="w-full min-w-20 bg-white border border-gray-400 rounded-lg px-3 py-1 text-sm text-gray-700 cursor-pointer "
            >
              <option value="">すべて</option>
              <option value="NVIDIA_JETSON">NVIDIA Jetson</option>
              <option value="RASPBERRY_PI">Raspberry Pi</option>
            </select>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-gray-800 text-sm whitespace-nowrap">
            ステータス:
          </label>
          <div className="w-40">
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="w-full min-w-20 bg-white border border-gray-400 rounded-lg px-3 py-1 text-sm text-gray-700 cursor-pointer"
            >
              <option value="">すべて</option>
              <option value="ACTIVE">有効</option>
              <option value="BETA">ベータ版</option>
              <option value="DEPRECATED">非推奨</option>
            </select>
          </div>
        </div>
        <div className="relative min-w-[150px]">
          <Input
            placeholder="ソリューションを検索…"
            className="h-[30px] w-full bg-white border border-gray-400 rounded-full pr-12 pl-3 py-1 text-sm text-gray-700 focus:outline-none focus:ring-1 focus:ring-gray-500"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          {/* No entry icon — flipped line */}
          <div className="absolute inset-y-0 right-3 flex items-center pointer-events-none">
            <Search color="gray" />
          </div>
        </div>
      </div>
    </div>
  );
}
