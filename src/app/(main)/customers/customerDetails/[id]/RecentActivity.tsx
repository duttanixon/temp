const activityItems = [
  { time: '2h ago', message: 'Device DEV-JP-001293 updated configuration' },
  { time: 'Yesterday', message: 'New user Yuki Sato added' },
  { time: '3d ago', message: 'Solution CityEye upgraded to v3.2.1' },
];

export default function RecentActivity() {
  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200 flex flex-col h-[340px] mt-10">
      <h2 className="text-lg font-bold mb-4 text-gray-800">Recent Activity</h2>
      <hr className="mb-4" />
      <ul className="text-sm text-gray-700 divide-y divide-gray-200 flex-1">
        {activityItems.map((item, idx) => (
          <li key={idx} className="flex justify-between py-3">
            <span>{item.message}</span>
            <span className="text-gray-500">{item.time}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}