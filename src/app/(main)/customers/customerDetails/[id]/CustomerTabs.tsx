'use client';

import { useState } from 'react';

const tabs = [
  'Overview',
  'Devices',
  'Users',
  'Subscription',
  'Solutions',
  'Billing',
  'Support',
  'Settings',
];

export default function CustomerTabs() {
  const [selectedTab, setSelectedTab] = useState('Overview');

  return (
    <div className="flex mb-6 bg-white rounded-md overflow-hidden border border-gray-200">
      {tabs.map((tab) => (
        <button
          key={tab}
          onClick={() => setSelectedTab(tab)}
          className={`flex-1 py-4 text-sm font-semibold text-center transition
            ${
              tab === selectedTab
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-100'
            }`}
        >
          {tab}
        </button>
      ))}
    </div>
  );
}