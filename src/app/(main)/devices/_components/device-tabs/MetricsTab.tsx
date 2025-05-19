export default function MetricsTab() {
  return (
    <div className="bg-inherit p-2 flex flex-col md:flex-row gap-4 items-stretch justify-center rounded-b-lg">
      <div className="bg-white p-4 rounded-lg shadow flex-1">
        <h2 className="text-lg font-semibold mb-2">Metrics Card 1</h2>
        <p className="text-gray-600">Content for the first metrics card</p>
      </div>

      <div className="bg-white p-4 rounded-lg shadow flex-1">
        <h2 className="text-lg font-semibold mb-2">Metrics Card 2</h2>
        <p className="text-gray-600">Content for the second metrics card</p>
      </div>
      <div className="bg-white p-4 rounded-lg shadow flex-1">
        <h2 className="text-lg font-semibold mb-2">Metrics Card 2</h2>
        <p className="text-gray-600">Content for the second metrics card</p>
      </div>
    </div>
  );
}
