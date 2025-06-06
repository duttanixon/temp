type Props = {
  deviceType: string;
  setDeviceType: (val: string) => void;
  status: string;
  setStatus: (val: string) => void;
};

export default function SolutionFilters({
  deviceType,
  setDeviceType,
  status,
  setStatus,
}: Props) {
  return (
    <div className="relative border border-gray-400 rounded-md px-4 py-3 w-2/5 bg-white overflow-hidden">
      <div className="flex items-center gap-6 flex-nowrap">
        <label className="text-gray-800 text-sm whitespace-nowrap">
          互換デバイス:
        </label>
        <div className="relative w-40">
          <select
            value={deviceType}
            onChange={(e) => setDeviceType(e.target.value)}
            className="w-full bg-white border border-gray-400 rounded-lg px-3 py-1 text-sm text-gray-700"
          >
            <option value="">すべて</option>
            <option value="NVIDIA_JETSON">NVIDIA Jetson</option>
            <option value="RASPBERRY_PI">Raspberry Pi</option>
          </select>
        </div>

        <label className="text-gray-800 text-sm whitespace-nowrap">
          ステータス:
        </label>
        <div className="relative w-40">
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="w-full bg-white border border-gray-400 rounded-lg px-3 py-1 text-sm text-gray-700"
          >
            <option value="">すべて</option>
            <option value="ACTIVE">有効</option>
            <option value="BETA">ベータ版</option>
            <option value="DEPRECATED">非推奨</option>
          </select>
        </div>
      </div>
    </div>
  );
}
