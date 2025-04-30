interface StatCardProps {
  title: string;
  value: string;
  highlight?: boolean;
}

const StatCard = ({ title, value, highlight }: StatCardProps) => (
  <div className="bg-white p-4 rounded shadow min-h-[120px] flex flex-col justify-between text-center">
    <p className="text-gray-500 text-sm">{title}</p>
    <p className={`text-2xl font-bold ${highlight ? 'text-green-600' : 'text-gray-800'}`}>
      {value}
    </p>
  </div>
);

export default function CustomerStats() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <StatCard title="Active Devices" value="22 / 30" />
      <StatCard title="User Accounts" value="8 / 15" highlight />
      <StatCard title="Renewal Date" value="Jul 15, 2025" />
      <StatCard title="Open Alerts" value="3" />
    </div>
  );
}