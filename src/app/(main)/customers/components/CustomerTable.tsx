// File: app/(main)/customers/components/CustomerTable.tsx
'use client'

import CustomerPagination from '@/app/(main)/customers/components/Pagination'
import CustomerDetailModal from '@/app/(main)/customers/components/CustomerDetailModal'
import CustomerEditModal from '@/app/(main)/customers/components/CustomerEditModal'
import { useState } from 'react'

interface Customer {
  customer_id: string
  name: string
  contact_email: string
  address: string
  status: string
  created_at: string
}

interface CustomerTableProps {
  customers: Customer[]
  page: number
  setPage: (page: number) => void
  itemsPerPage: number
}

export default function CustomerTable({
  customers,
  page,
  setPage,
  itemsPerPage
}: CustomerTableProps) {
  const [detailOpen, setDetailOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null)

  const paginated = customers.slice(page * itemsPerPage, (page + 1) * itemsPerPage)
  const totalItems = customers.length

  const openDetail = (customer: Customer) => {
    setSelectedCustomer(customer)
    setDetailOpen(true)
  }

  const openEdit = (customer: Customer) => {
    setSelectedCustomer(customer)
    setEditOpen(true)
  }

  return (
    <div className="space-y-4">
      <div className="border rounded overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-100 text-left">
            <tr>
              <th className="p-2">Customer Name</th>
              <th>Contact Email</th>
              <th>Address</th>
              <th>Status</th>
              <th>Created On</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {paginated.map((customer) => (
              <tr className="border-t" key={customer.customer_id}>
                <td className="p-2">{customer.name}</td>
                <td>{customer.contact_email}</td>
                <td>{customer.address}</td>
                <td>
                  <span className={`text-xs font-medium px-2 py-1 rounded-full ${
                    customer.status === 'ACTIVE'
                      ? 'bg-green-100 text-green-700'
                      : customer.status === 'INACTIVE'
                      ? 'bg-yellow-100 text-yellow-700'
                      : 'bg-gray-100 text-gray-700'
                  }`}>
                    {customer.status}
                  </span>
                </td>
                <td>
                  <span className="bg-gray-100 text-gray-800 text-xs font-medium px-2 py-1 rounded-full">
                    {new Date(customer.created_at).toLocaleDateString()}
                  </span>
                </td>
                <td className="space-x-2">
                  <button
                    className="bg-blue-100 text-blue-700 text-xs font-medium px-2 py-1 rounded"
                    onClick={() => openEdit(customer)}
                  >
                    Edit
                  </button>
                  <button
                    className="bg-red-100 text-red-700 text-xs font-medium px-2 py-1 rounded"
                    onClick={() => openDetail(customer)}
                  >
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <CustomerPagination
        page={page}
        setPage={setPage}
        totalItems={totalItems}
        itemsPerPage={itemsPerPage}
      />

      <CustomerDetailModal open={detailOpen} onOpenChange={setDetailOpen} customer={selectedCustomer} />
      <CustomerEditModal open={editOpen} onOpenChange={setEditOpen} customer={selectedCustomer} onSubmit={() => {}} />
    </div>
  )
}