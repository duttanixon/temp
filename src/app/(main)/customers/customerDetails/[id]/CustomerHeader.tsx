interface CustomerHeaderProps {
    name: string;
    customerId: string;
    status: string;
  }
  
  export default function CustomerHeader({ name, customerId, status }: CustomerHeaderProps) {
    return (
      <div className="flex justify-between items-center mb-4">
        <div>
          <h1 className="text-2xl font-semibold">{name} Overview</h1>
          <p className="text-sm text-gray-600">Customer ID: {customerId} </p>
          <p className="text-sm text-gray-600"> Status: {status}</p>
        </div>
        <div className="space-x-4">
          <button className="px-6 py-3 rounded-lg bg-blue-500 text-white font-semibold hover:bg-blue-700 transition">
            Edit Details
          </button>
          <button className="px-6 py-3 rounded-lg bg-red-500 text-white font-semibold hover:bg-red-700 transition">
            Suspend
          </button>
        </div>
      </div>
    );
  }