'use client';

import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { useState } from 'react';

export default function EditCustomerPage() {
  const [companyName, setCompanyName] = useState('Tokyo Metro Co., Ltd.');
  const [businessType, setBusinessType] = useState('Transportation');
  const [contactEmail, setContactEmail] = useState('admin@tokyometro.jp');
  const [contactPhone, setContactPhone] = useState('+81 3-3837-7111');
  const [address, setAddress] = useState('3-19-6 Higashi-Ueno, Taito-ku');
  const [accountStatus, setAccountStatus] = useState('Active');

  const handleSave = () => {
    console.log('Saving customer:', {
      companyName,
      businessType,
      contactEmail,
      contactPhone,
      address,
      accountStatus,
    });
    // TODO: Connect to API
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-2">Edit Customer: Tokyo Metro</h1>
      <p className="text-sm text-gray-500 mb-6">Customer ID: TKM-20230815</p>

      <div className="bg-white p-6 rounded-lg border border-gray-200 space-y-6">

        {/* Tabs */}
        <div className="flex space-x-4 border-b pb-4">
          <button className="px-4 py-2 bg-blue-600 text-white rounded">Basic Info</button>
          <button className="px-4 py-2 bg-gray-100 text-gray-700 rounded">Contact</button>
          <button className="px-4 py-2 bg-gray-100 text-gray-700 rounded">Subscription</button>
          <button className="px-4 py-2 bg-gray-100 text-gray-700 rounded">Users</button>
          <button className="px-4 py-2 bg-gray-100 text-gray-700 rounded">Solutions</button>
          <button className="px-4 py-2 bg-gray-100 text-gray-700 rounded">Devices</button>
          <button className="px-4 py-2 bg-gray-100 text-gray-700 rounded">Settings</button>
        </div>

        {/* Form */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-800 mb-2">Company Information</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

            {/* Left Column */}
            <div className="space-y-4">
              <div>
                <Label>Company Name *</Label>
                <Input
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  placeholder="Enter company name"
                />
              </div>
            </div>

            {/* Right Column */}
            <div className="space-y-4">
              <div>
                <Label>Business Type</Label>
                <Input
                  value={businessType}
                  onChange={(e) => setBusinessType(e.target.value)}
                  placeholder="Enter business type"
                />
              </div>
            </div>
          </div>

          {/* Contact Email + Contact Phone, side-by-side and each 50% of the full card width */}
          <div className="flex flex-col md:flex-row gap-6">
            <div className="w-full md:w-1/2">
              <Label>Contact Email *</Label>
              <Input
                value={contactEmail}
                onChange={(e) => setContactEmail(e.target.value)}
                placeholder="Enter contact email"
              />
            </div>
            <div className="w-full md:w-1/2">
              <Label>Contact Phone *</Label>
              <Input
                value={contactPhone}
                onChange={(e) => setContactPhone(e.target.value)}
                placeholder="Enter contact phone"
              />
            </div>
          </div>

          {/* Address (full width) */}
          <div>
            <Label>Address *</Label>
            <Textarea
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="Enter address"
              rows={3}
            />
          </div>

          {/* Account Status (half width) */}
          <div className="w-1/2">
            <Label>Account Status *</Label>
            <select
              value={accountStatus}
              onChange={(e) => setAccountStatus(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm text-gray-800 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="Active">Active</option>
              <option value="Suspended">Suspended</option>
              <option value="Inactive">Inactive</option>
              <option value="Pending">Pending</option>
            </select>
          </div>
        </div>

        {/* Buttons */}
        <div className="flex justify-start space-x-4 pt-4">
          <Button onClick={handleSave}>Save</Button>
          <Button variant="outline">Cancel</Button>
        </div>

      </div>
    </div>
  );
}