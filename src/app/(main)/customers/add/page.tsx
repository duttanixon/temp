'use client';

import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function AddCustomerPage() {
  const router = useRouter();

  const [companyName, setCompanyName] = useState('');
  const [contactEmail, setContactEmail] = useState('');
  const [address, setAddress] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/customers', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json'
        },
        body: JSON.stringify({
          name: companyName,
          contact_email: contactEmail,
          address,
          status: 'ACTIVE' // optional default
        })
      });

      if (!res.ok) {
        const error = await res.text();
        throw new Error(error || 'Failed to create customer');
      }

      const data = await res.json();
      console.log('Customer created:', data);

      // Redirect or show success
      router.push('/customers'); // redirect to customer list page
    } catch (error) {
      console.error('Submit error:', error);
      alert('Failed to create customer');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-2">Add New Customer</h1>
      <p className="text-sm text-gray-500 mb-6">Customers &gt; Add New Customer</p>

      <div className="bg-white p-6 rounded-lg border border-gray-200 space-y-6">
        {/* Tabs */}
        <div className="flex space-x-4 border-b pb-4">
          <button className="px-4 py-2 bg-blue-600 text-white rounded">Basic Info</button>
          <button className="px-4 py-2 bg-gray-100 text-gray-700 rounded">Subscription</button>
        </div>

        {/* Form */}
        <div className="space-y-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-2">
            Company Information <span className="text-sm text-gray-400 ml-2">* Required fields</span>
          </h2>

          <div className="space-y-4">
            {/* Company Name */}
            <div className="w-1/2">
              <Label>Company Name *</Label>
              <Input
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                placeholder="Enter company name"
              />
            </div>

            {/* Contact Email */}
            <div className="w-1/2">
              <Label>Contact Email *</Label>
              <Input
                type="email"
                value={contactEmail}
                onChange={(e) => setContactEmail(e.target.value)}
                placeholder="Enter contact email"
              />
            </div>

            {/* Address */}
            <div className="w-1/2">
              <Label>Address</Label>
              <Textarea
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                placeholder="Enter address"
                rows={3}
              />
            </div>
          </div>
        </div>

        {/* Buttons */}
        <div className="flex justify-start space-x-4 pt-4">
          <Button onClick={handleSubmit} disabled={loading}>
            {loading ? 'Creating...' : 'Create'}
          </Button>
          <Button variant="outline" onClick={() => router.back()}>Cancel</Button>
        </div>
      </div>
    </div>
  );
}