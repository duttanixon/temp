interface CustomerProfileProps {
  name: string;
  address: string;
  createdAt: string;
  accountManager: string;
}

export default function CustomerProfile({ name, address, createdAt, accountManager }: CustomerProfileProps) {
  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200 flex flex-col h-[400px]">
      <h2 className="text-lg font-bold mb-2 text-gray-800">Customer Profile</h2>
      <hr className="mb-4" />
      
      <h3 className="text-xl font-semibold text-gray-800 mb-6">{name}</h3>

      <div className="text-sm text-gray-700 flex-1 space-y-4">
        <div className="flex">
          <span className="text-gray-500 w-40">Address:</span>
          <div>{address}</div>
        </div>

        <div className="flex">
          <span className="text-gray-500 w-40">Customer Since:</span>
          <span>{new Date(createdAt).toLocaleDateString('en-US', {
              year: 'numeric',
              month: 'long',
              day: 'numeric'
            })}
          </span>
        </div>

        <div className="flex">
          <span className="text-gray-500 w-40">Account Manager:</span>
          <span>{accountManager}</span>
        </div>
      </div>
    </div>
  );
}