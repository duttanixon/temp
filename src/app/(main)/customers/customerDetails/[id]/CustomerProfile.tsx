export default function CustomerProfile() {
  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200 flex flex-col h-[400px]">
      <h2 className="text-lg font-bold mb-2 text-gray-800">Customer Profile</h2>
      <hr className="mb-4" />
      
      {/* Customer Name */}
      <h3 className="text-xl font-semibold text-gray-800 mb-6">Tokyo Metro</h3>

      <div className="text-sm text-gray-700 flex-1 space-y-4">
        
        {/* Address */}
        <div className="flex">
          <span className="text-gray-500 w-40">Address:</span>
          <div>
            3-19-6 Higashi-Ueno<br />
            Taito-ku, Tokyo 110-8614<br />
            Japan
          </div>
        </div>

        {/* Customer Since */}
        <div className="flex">
          <span className="text-gray-500 w-40">Customer Since:</span>
          <span>May 15, 2023</span>
        </div>

        {/* Account Manager */}
        <div className="flex">
          <span className="text-gray-500 w-40">Account Manager:</span>
          <span>Tanaka Hiroshi</span>
        </div>

      </div>
    </div>
  );
}