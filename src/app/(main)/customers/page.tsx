// File: app/(main)/customers/page.tsx
'use client'

import { useEffect, useState } from 'react'
import AddCustomerButton from '@/app/(main)/customers/components/AddCustomerButton'
import SearchFilters from '@/app/(main)/customers/components/SearchFilters'
import StatsCard from '@/app/(main)/customers/components/StatsCard'
import CustomerTable from '@/app/(main)/customers/components/CustomerTable'

interface Customer {
  customer_id: string
  name: string
  contact_email: string
  address: string
  status: string
  created_at: string
}

export default function CustomersPage() {
  const [allCustomers, setAllCustomers] = useState<Customer[]>([])
  const [filteredCustomers, setFilteredCustomers] = useState<Customer[]>([])
  const [page, setPage] = useState(0)

  useEffect(() => {
    const fetchCustomers = async () => {
      try {
        const res = await fetch('/api/customers?skip=0&limit=1000')
        const data = await res.json()
        const list = Array.isArray(data) ? data : Array.isArray(data.customers) ? data.customers : Array.isArray(data.data) ? data.data : []

        setAllCustomers(list)
        setFilteredCustomers(list)
      } catch (err) {
        console.error('Failed to fetch customers:', err)
      }
    }
    fetchCustomers()
  }, [])

  const handleSearch = (query: string, status: string, region: string) => {
    let filtered = allCustomers

    if (status !== 'All Statuses') {
      filtered = filtered.filter(c => c.status.toLowerCase() === status.toLowerCase())
    }

    if (region !== 'All Regions') {
      filtered = filtered.filter(c => c.address.toLowerCase().includes(region.toLowerCase()))
    }

    if (query) {
      const q = query.toLowerCase()
      filtered = filtered.filter(c =>
        c.name.toLowerCase().includes(q) ||
        c.contact_email.toLowerCase().includes(q)
      )
    }

    setFilteredCustomers(filtered)
    setPage(0) // reset page to 0 on new search
  }


  const total = allCustomers.length
  const active = allCustomers.filter(c => c.status === 'ACTIVE').length
  const devices = allCustomers.length

  return (
    <div className="space-y-6 px-6 pt-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Customer Management</h1>
        <AddCustomerButton />
      </div>

      <SearchFilters onSearch={handleSearch} />

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatsCard title="Total Customers" value={total} />
        <StatsCard title="Active Customers" value={active} colorClass="text-green-600" />
        <StatsCard title="Total Devices" value={devices} colorClass="text-blue-600" />
      </div>

      <CustomerTable
        customers={filteredCustomers}
        page={page}
        setPage={setPage}
        itemsPerPage={5}
        />
    </div>
  )
}
