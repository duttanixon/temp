'use client'

import { useEffect, useState } from 'react'
import CustomerHeader from '@/app/(main)/customers/customerDetails/[id]/CustomerHeader'
import CustomerTabs from '@/app/(main)/customers/customerDetails/[id]/CustomerTabs'
import CustomerStats from '@/app/(main)/customers/customerDetails/[id]/CustomerStats'
import CustomerProfile from '@/app/(main)/customers/customerDetails/[id]/CustomerProfile'
import RecentActivity from '@/app/(main)/customers/customerDetails/[id]/RecentActivity'

interface Props {
  customerId: string;
}

interface Customer {
  customer_id: string;
  name: string;
  address: string;
  contact_email: string;
  status: string;
  created_at: string;
  account_manager?: string; // if available
}

export default function CustomerOverviewPage({ customerId }: Props) {
  const [customer, setCustomer] = useState<Customer | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    const fetchCustomer = async () => {
      try {
        const res = await fetch(`/api/customers/${customerId}`)
        if (!res.ok) throw new Error('Failed to fetch')
        const data = await res.json()
        setCustomer(data)
      } catch (err) {
        console.error(err)
        setError(true)
      } finally {
        setLoading(false)
      }
    }

    fetchCustomer()
  }, [customerId])

  if (loading) return <div className="p-6 text-gray-500">Loading...</div>
  if (error || !customer) return <div className="p-6 text-red-600">Failed to load customer data.</div>

  return (
    <div className="p-6 space-y-6">
      <CustomerHeader
        name={customer.name}
        customerId={customer.customer_id}
        status={customer.status}
      />
      <CustomerTabs />
      <CustomerStats />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-end">
        <div className="md:col-span-2">
          <CustomerProfile
            name={customer.name}
            address={customer.address}
            createdAt={customer.created_at}
            accountManager={customer.account_manager || 'N/A'}
          />
        </div>
        <RecentActivity />
      </div>
    </div>
  )
}